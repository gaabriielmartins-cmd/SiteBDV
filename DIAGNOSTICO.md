# Diagnóstico gratuito do SiteBDV

Requer Python 3.10 ou superior. Usa somente a biblioteca padrão. Mantenha o Waitress aberto e execute em outro terminal PowerShell.

## Uso

```powershell
& '.\.venv\Scripts\python.exe' .\diagnostico.py http://127.0.0.1:5000
```

Diagnóstico público com comparação local (execute no computador que hospeda o site):

```powershell
& '.\.venv\Scripts\python.exe' .\diagnostico.py https://0vg2752v-5000.brs.devtunnels.ms --local http://127.0.0.1:5000
```

Carga opcional, somente em servidores próprios/autorizados:

```powershell
& '.\.venv\Scripts\python.exe' .\diagnostico.py http://127.0.0.1:5000 --usuarios 50 --segundos 120
```

Padrão: um usuário virtual por 30 segundos, pausando cinco segundos entre visitas. Limites: 100 usuários e 600 segundos. Cada usuário faz uma requisição por vez; usuários virtuais não equivalem a requisições simultâneas. A logo e a API são verificadas uma vez antes da carga; visitas repetidas medem a página principal. Não renderiza JavaScript nem carrega serviços externos.

## Relatório

Exibe resumo no terminal e salva `relatorio_DATA_HORA.json` na pasta atual. Inclui amostras, status HTTP, média, p95 (95% das respostas até esse tempo), falhas, resultados por rota e recomendações. Redirecionamentos não são seguidos, para detectar bloqueios de login. O cabeçalho de limite anunciado pelo intermediário é exibido quando disponível, sem atribuir automaticamente os erros a esse limite.

HTTP 503 pode vir do servidor ou de intermediários. Compare público e local: resultado local bom e público ruim é um indício de limitação no caminho externo, não uma prova da causa. Os testes são sequenciais e usam a mesma máquina como gerador de carga, o que pode afetar os resultados. Não coleta CPU/RAM nem logs do servidor; essas informações exigem monitoramento adicional. Tempos incluem conexão e leitura da resposta (até 2 MB).

Interrompe a carga se as últimas 100 respostas tiverem pelo menos 20% de falhas ou p95 acima de 10 segundos. Requisições em andamento podem levar até o timeout de 15 segundos para terminar. Se a página inicial falhar na verificação, a carga não começa. Os três acessos iniciais entram no resumo geral. Duração real pode exceder a solicitada por pausas e requisições em andamento. Resultado sem falhas em uma amostra não comprova capacidade máxima.
