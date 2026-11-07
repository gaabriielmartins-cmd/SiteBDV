import argparse
import collections
import concurrent.futures
import gzip
import io
import ipaddress
import json
import math
import statistics
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib
from pathlib import Path


class SemRedirecionar(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def criar_cliente(base):
    """Um cliente por usuário; loopback não precisa descobrir proxies do Windows."""
    host = urllib.parse.urlsplit(base).hostname or ''
    try:
        local = ipaddress.ip_address(host).is_loopback
    except ValueError:
        local = host.lower() == 'localhost'
    handlers = [SemRedirecionar()]
    if local:
        handlers.append(urllib.request.ProxyHandler({}))
    # Para URLs externas, preserva proxies e certificados configurados.
    return urllib.request.build_opener(*handlers)


def consultar(base, rota, cliente=None, comprimir=False):
    if cliente is None:
        cliente = criar_cliente(base)
    inicio = time.monotonic()
    status, erro, headers, corpo, recebidos = 0, '', {}, b'', 0
    try:
        req = urllib.request.Request(base.rstrip('/') + rota,
                                     headers={'User-Agent': 'DiagnosticoBDV/1.1',
                                              'Accept-Encoding': 'gzip' if comprimir else 'identity'})
        with cliente.open(req, timeout=15) as resposta:
            status = resposta.status
            headers = dict(resposta.headers.items())
            corpo = resposta.read(2_000_001)
            recebidos = len(corpo)
    except urllib.error.HTTPError as exc:
        status = exc.code
        headers = dict(exc.headers.items())
        erro = 'HTTP ' + str(status)
    except Exception as exc:
        erro = type(exc).__name__ + ': ' + str(exc)
    headers = {k.lower(): v for k, v in headers.items()}
    if status == 200 and not erro and headers.get('content-encoding', '').lower() == 'gzip':
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(corpo)) as arquivo:
                corpo = arquivo.read(2_000_001)
        except (OSError, EOFError, ValueError, zlib.error) as exc:
            erro = 'Gzip invalido: ' + str(exc)
    if status == 200 and not erro:
        if len(corpo) > 2_000_000:
            erro = 'Resposta maior que 2 MB; leitura limitada'
        elif rota == '/' and b'<title>Batata Das Vargens' not in corpo:
            erro = 'Pagina diferente do SiteBDV'
        elif rota.endswith('.png') and not corpo.startswith(b'\x89PNG\r\n\x1a\n'):
            erro = 'Logo invalida'
        elif rota == '/api/cardapio':
            try:
                if not isinstance(json.loads(corpo), dict):
                    erro = 'Cardapio nao e um objeto JSON'
            except (ValueError, UnicodeError):
                erro = 'Cardapio com JSON invalido'
    return dict(rota=rota, status=status, erro=erro,
                ms=round((time.monotonic() - inicio) * 1000, 1),
                bytes_recebidos=recebidos,
                headers={k: v for k, v in headers.items()
                         if k in ('server', 'ratelimit-limit', 'retry-after',
                                  'content-encoding', 'etag')})


def resumir(linhas):
    tempos = sorted(r['ms'] for r in linhas)
    return dict(requisicoes=len(linhas),
                falhas=sum(bool(r['erro']) for r in linhas),
                media_ms=round(statistics.mean(tempos), 1),
                p95_ms=tempos[math.ceil(len(tempos) * .95) - 1],
                status=dict(collections.Counter(str(r['status']) for r in linhas)))


def analisar(linhas):
    alertas = []
    codigos = {r['status'] for r in linhas}
    if codigos & {301, 302, 303, 307, 308, 401, 403}:
        alertas.append('Acesso restrito ou redirecionado: confira a visibilidade do tunel.')
    if 429 in codigos:
        alertas.append('Limite de requisicoes atingido. Respeite Retry-After e reduza a carga.')
    if 503 in codigos:
        alertas.append('HTTP 503: indisponibilidade no servidor ou intermediario. Compare com localhost.')
    if codigos & {500, 502, 504}:
        alertas.append('Erro de servidor/proxy: confira os logs do Waitress e do tunel.')
    if 0 in codigos:
        alertas.append('Falha de conexao ou timeout: confira internet, porta e servidor.')
    if 404 in codigos:
        alertas.append('Rota ou arquivo ausente: confira /api/cardapio e static/logo.png.')
    if resumir(linhas)['p95_ms'] > 2000:
        alertas.append('p95 acima de 2 segundos: resposta lenta neste cenario.')
    limites = sorted({r['headers']['ratelimit-limit'] for r in linhas
                      if 'ratelimit-limit' in r['headers']})
    if limites:
        alertas.append('Limites anunciados pelo intermediario: ' + ', '.join(limites))
    if any('werkzeug' in r['headers'].get('server', '').lower() for r in linhas):
        alertas.append('Servidor de desenvolvimento detectado. Use Waitress.')
    if any(r['status'] == 200 and r['erro'] for r in linhas):
        alertas.append('Houve HTTP 200 com conteudo inesperado; confira a pagina e os arquivos.')
    return alertas or ['Nenhum problema detectado nesta amostra; isso nao garante capacidade maxima.']


def executar(url, usuarios, segundos, comprimir=False):
    cliente = criar_cliente(url)
    linhas = [consultar(url, rota, cliente, comprimir)
              for rota in ('/', '/static/logo.png', '/api/cardapio')]
    inicio = time.monotonic()
    parar = threading.Event()
    lock = threading.Lock()
    motivo = ''
    preparos = []
    if linhas[0]['erro']:
        return dict(url=url, resumo=resumir(linhas), alertas=analisar(linhas),
                    motivo='Carga nao iniciada: pagina inicial falhou.', amostras=linhas)

    def usuario():
        preparo = time.monotonic()
        cliente_usuario = criar_cliente(url)
        with lock:
            preparos.append((time.monotonic() - preparo) * 1000)
        while time.monotonic() - inicio < segundos and not parar.is_set():
            resultado = consultar(url, '/', cliente_usuario, comprimir)
            with lock:
                linhas.append(resultado)
                recentes = linhas[-100:]
                if len(recentes) == 100:
                    s = resumir(recentes)
                    if s['falhas'] >= 20 or s['p95_ms'] > 10000:
                        parar.set()
            parar.wait(min(5, max(0, segundos - (time.monotonic() - inicio))))

    with concurrent.futures.ThreadPoolExecutor(max_workers=usuarios) as pool:
        tarefas = [pool.submit(usuario) for _ in range(usuarios)]
        for tarefa in tarefas:
            tarefa.result()
    if parar.is_set():
        motivo = 'Interrompido: >=20% de falhas ou p95 >10s nas ultimas 100 respostas.'
    return dict(url=url, usuarios_virtuais=usuarios,
                versao_diagnostico='1.1', gzip_solicitado=comprimir,
                preparo_medio_cliente_ms=round(statistics.mean(preparos), 1),
                duracao_real_s=round(time.monotonic() - inicio, 1),
                resumo=resumir(linhas), motivo=motivo,
                por_rota={rota: resumir([r for r in linhas if r['rota'] == rota])
                          for rota in sorted({r['rota'] for r in linhas})},
                alertas=analisar(linhas), amostras=linhas)


def main():
    parser = argparse.ArgumentParser(description='Diagnostico gratuito do SiteBDV')
    parser.add_argument('url')
    parser.add_argument('--local', help='URL local opcional para comparar')
    parser.add_argument('--usuarios', type=int, default=1)
    parser.add_argument('--segundos', type=int, default=30)
    parser.add_argument('--gzip', action='store_true', help='Solicita e valida gzip')
    args = parser.parse_args()
    if not 1 <= args.usuarios <= 100 or not 1 <= args.segundos <= 600:
        parser.error('Use 1 a 100 usuarios e 1 a 600 segundos.')
    urls = [args.url] + ([args.local] if args.local else [])
    for url in urls:
        if urllib.parse.urlsplit(url).scheme not in ('http', 'https'):
            parser.error('As URLs precisam comecar com http:// ou https://')
    relatorios = []
    for url in urls:
        print('Analisando', url, '- aguarde...', flush=True)
        r = executar(url, args.usuarios, args.segundos, args.gzip)
        relatorios.append(r)
        print(json.dumps({k: v for k, v in r.items() if k != 'amostras'},
                         ensure_ascii=False, indent=2))
    destino = Path('relatorio_' + time.strftime('%Y%m%d_%H%M%S') + '.json')
    destino.write_text(json.dumps(relatorios, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Relatorio salvo em:', destino.resolve())
    print('Os tempos incluem a rede. Compare local e publico; os testes sao sequenciais.')


if __name__ == '__main__':
    main()
