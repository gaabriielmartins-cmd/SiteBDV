# Melhorias de desempenho no Flask

O cardápio e o HTML são iguais para todos os visitantes. Em produção, cada processo renderiza a página e serializa o JSON uma vez ao iniciar. As requisições seguintes reutilizam bytes imutáveis; cada uma recebe um Response novo para evitar compartilhamento de estado entre threads.

HTML e JSON têm versões gzip pré-computadas. A negociação respeita Accept-Encoding e as preferências q; clientes sem gzip continuam recebendo os bytes originais. Cada representação possui seu próprio ETag e Vary: Accept-Encoding. O navegador pode revalidar e receber 304 sem corpo quando o conteúdo não muda. Cache-Control: no-cache exige revalidação antes de reutilizar HTML/JSON, para não mostrar preços antigos depois de reiniciar o servidor. Arquivos estáticos podem ser reutilizados por uma hora (substituições da logo podem levar esse tempo para aparecer no navegador).

## Executar no Windows

Mantenha as dependências atuais e o Waitress já instalado. Depois de baixar esta branch, pare o servidor anterior com Ctrl+C e execute no Git Bash:

```bash
./.venv/Scripts/python.exe -m waitress --listen=0.0.0.0:5000 --threads=8 banco_de_dados:app
```

Ao editar o cardápio, os dados da loja ou o template, reinicie o Waitress para reconstruir o cache. O modo de desenvolvimento debug continua renderizando os dados a cada acesso. O cache foi feito para as duas rotas públicas atuais; se adicionar personalização por usuário, revise essa estratégia.

## Validar

```bash
./.venv/Scripts/python.exe -m unittest discover -s tests -v
./.venv/Scripts/python.exe diagnostico.py http://127.0.0.1:5000 --usuarios 100 --segundos 120
```

Seis testes cobrem equivalência com o conteúdo renderizado, JSON, gzip, negociação com qualidades e exclusões, ETags por representação, GET condicional, HEAD, Vary, atualização em debug, ausência de renderização/serialização por requisição e isolamento com acessos concorrentes.

Comparação na máquina de desenvolvimento: cinco rodadas de 300 GETs via Flask test_client, após aquecimento. Mediana do tempo por requisição: 0,4233 ms antes e 0,1381 ms depois (aproximadamente 3,07x). HTML: 42.229 bytes original e 8.522 bytes gzip (redução de 79,8%). O conteúdo descomprimido foi comparado com a versão original. Esses números medem o caminho interno da aplicação, sem Waitress, rede, túnel ou renderização do navegador. Não equivalem ao tempo observado no computador do usuário nem garantem capacidade para 1.000 usuários. Repita o diagnóstico local para medir o ganho real no seu ambiente.
