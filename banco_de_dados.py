# -*- coding: utf-8 -*-
"""
banco-de-dados.py
------------------
Backend Flask do site do Batata Das Vargens.

Este arquivo tem duas funções:
1) Guardar os dados do cardápio (o "banco de dados" do site).
2) Servir o site (siteBDV.html) usando esses dados.

COMO EDITAR O CARDÁPIO
-----------------------
Basta mexer no dicionário MENU lá embaixo. Cada categoria é uma chave,
e cada item é um dicionário com "nome", "descricao" e "preco".
Não precisa mexer em mais nada — o site se atualiza sozinho.

COMO RODAR
----------
1) Instale o Flask (uma vez só):
       pip install flask
2) Rode o servidor:
       python banco-de-dados.py
3) Abra no navegador:
       http://localhost:5000

ESTRUTURA DE PASTAS ESPERADA
-----------------------------
    siteBDV/
    ├── static/
    │   └── logo.png        <- imagens ficam aqui dentro
    ├── banco-de-dados.py   <- este arquivo
    └── siteBDV.html        <- o template do site
"""

# 'os' é usado só para descobrir o caminho da pasta onde este arquivo está,
# assim o Flask sabe onde procurar o siteBDV.html e a pasta static/,
# não importa de onde você rode o comando "python banco-de-dados.py".
import os

# Flask   -> cria e configura o servidor web (a "aplicação")
# render_template -> pega o siteBDV.html e substitui as variáveis {{ }} pelos dados reais
# jsonify -> transforma um dicionário Python em resposta JSON (usado na rota /api/cardapio)
from flask import Flask, render_template, jsonify

# ==========================================================================
# CONFIGURAÇÕES GERAIS DO ESTABELECIMENTO
# ==========================================================================
# Tudo que aparece "fixo" no site (fora do cardápio) fica centralizado aqui.
# Se mudar o WhatsApp, o Instagram, o endereço ou o horário, é só editar
# essas variáveis — elas são usadas automaticamente em várias partes do site
# (hero, seção de contato, rodapé e botão flutuante).

NOME_LOJA = "Batata Das Vargens"
TAGLINE = "Hambúrguers delicios, batata frita e combos que mata sua fome nas Vargens"

# Número de WhatsApp no formato internacional, só números (sem espaço, +, ( ) ou -).
# Ex: 55 (Brasil) + 21 (DDD) + número
WHATSAPP_NUMERO = "5521972749663"

# Mensagem que já vem pronta quando o cliente clica no botão de WhatsApp do site.
WHATSAPP_MENSAGEM_PADRAO = "Olá! Vi o cardápio do Batata Das Vargens pelo seu site e quero fazer um pedido"

# Monta o link final do WhatsApp juntando número + mensagem.
# O .replace(" ", "%20") troca espaços por "%20", que é como uma URL
# representa espaço em branco (senão o link quebra).
WHATSAPP_LINK = f"https://wa.me/{WHATSAPP_NUMERO}?text={WHATSAPP_MENSAGEM_PADRAO}".replace(" ", "%20")

# Usuário e link do Instagram, mostrados na seção de contato do site.
INSTAGRAM_USER = "@batatadasvargens"
INSTAGRAM_LINK = "https://www.instagram.com/batatadasvargens/"

# Endereço e horário de funcionamento, mostrados no rodapé do site.
# HORARIO_FUNCIONAMENTO é uma lista: cada item vira uma linha no rodapé.
ENDERECO = "Rua Manuel Bastos de Oliveira 21, Vargem Pequena, Rio de Janeiro - RJ"
HORARIO_FUNCIONAMENTO = [
    "Terça a Domingo: 18h às 23h",
    "Segunda: fechado",
]

# ==========================================================================
# CARDÁPIO — edite aqui os itens, descrições e preços
# ==========================================================================
# MENU é um dicionário onde:
#   - cada CHAVE é o nome de uma categoria (ex: "Combos", "Burguers")
#   - cada VALOR é uma LISTA de itens dessa categoria
#   - cada item é um dicionário com 3 campos:
#       "nome"      -> nome do produto (aparece em negrito no site)
#       "descricao" -> texto menor abaixo do nome (ingredientes, tamanho, etc.)
#       "preco"     -> número (use PONTO para centavos, nunca vírgula.
#                      Ex: 24.90 e não 24,90)
#
# A ORDEM das categorias aqui embaixo é a MESMA ordem que aparece no site
# (de cima para baixo). Quer mudar a ordem de exibição? Só reordenar os
# blocos de categoria aqui.
#
# Para ADICIONAR um item novo: copie um bloco {...} inteiro (com a vírgula
# no final) e cole dentro da categoria desejada, depois só trocar os valores.
#
# Para ADICIONAR uma categoria nova: copie o padrão
#     "Nome da Categoria": [ ... ],
# e cole em qualquer lugar dentro do MENU = { ... }.

MENU = {

    # ----------------------------------------------------------------
    # COMBOS — pacotes maiores, geralmente para dividir/compartilhar
    # ----------------------------------------------------------------
    "Combos": [
        {
            "nome": "Combo das Vargens",
            "descricao": "2 cheese burguers + 500g de batata + 10 salgadinhos à sua escolha.",
            "preco": 59.90,
        },
        {
            "nome": "Combo Alegria",
            "descricao": "250g de batata + 250g de frango à passarinho + 250g de linguiça calabresa acebolada.",
            "preco": 63.90,
        },
        {
            "nome": "Mega Combo",
            "descricao": "Batata 1kg + refrigerante 2L.",
            "preco": 64.90,
        },
        {
            "nome": "Combo Feliz",
            "descricao": "Batata 1kg + 10 salgadinhos à sua escolha.",
            "preco": 64.90,
        },
        {
            "nome": "Combo Mania de Cheddar",
            "descricao": "2 cheese burguers com cheddar e bacon + 250g de anéis de cebola.",
            "preco": 71.90,
        },
        {
            "nome": "Combo da Galera",
            "descricao": "Batata 1kg + anéis de cebola + frango à passarinho.",
            "preco": 78.90,
        },
        {
            "nome": "Combo Supremo",
            "descricao": "Batata 1kg + linguiça calabresa acebolada + frango à passarinho.",
            "preco": 79.90,
        },
        {
            "nome": "Combo Felicidade",
            "descricao": "4 cheese burguers + batata 1kg + 20 salgadinhos à escolha.",
            "preco": 94.90,
        },
        {
            "nome": "Combo Extreme",
            "descricao": "Batata 1kg + 40 anéis de cebola + linguiça calabresa acebolada + frango à passarinho.",
            "preco": 99.90,
        },
    ],

    # ----------------------------------------------------------------
    # BURGUERS — lanches individuais. "Furioso Burguer" é o
    # item de destaque do cardápio original, por isso vem primeiro.
    # ----------------------------------------------------------------
    "Hamburguers": [
        {
            "nome": "Furioso Burguer",
            "descricao": "Pão brioche, carne 150g, molho barbecue, queijo muçarela, bacon frito em cubos, 3 anéis de cebola, alface, tomate e cebola.",
            "preco": 29.90,
        },
        {
            "nome": "Classic Burguer",
            "descricao": "Pão, carne 100g, queijo muçarela, alface, tomate e cebola.",
            "preco": 9.90,
        },
        {
            "nome": "Classic Billy Bacon",
            "descricao": "Pão, carne 100g, queijo muçarela, molho billy jack e bacon.",
            "preco": 14.90,
        },
        {
            "nome": "Cheese Burguer",
            "descricao": "Pão, carne 100g, queijo muçarela, alface, tomate e cebola.",
            "preco": 14.90,
        },
        {
            "nome": "Steak Burguer",
            "descricao": "Pão, steak de frango, queijo muçarela, molho de mostarda, alface, tomate e cebola.",
            "preco": 17.90,
        },
        {
            "nome": "Cheese Cheddar",
            "descricao": "Pão, carne 100g, molho cheddar, queijo muçarela, alface, tomate e cebola.",
            "preco": 18.90,
        },
        {
            "nome": "Cheese Bacon",
            "descricao": "Pão, carne 100g, bacon em cubos, queijo muçarela, alface, tomate e cebola.",
            "preco": 18.90,
        },
        {
            "nome": "Cheese Egg",
            "descricao": "Pão, carne 100g, ovo frito, queijo muçarela, alface, tomate e cebola.",
            "preco": 19.90,
        },
        {
            "nome": "Cheese Onion",
            "descricao": "Pão, carne 100g, cebola caramelizada, queijo muçarela, alface, tomate e cebola.",
            "preco": 20.90,
        },
        {
            "nome": "X-Tudo",
            "descricao": "Pão, carne 100g, ovo frito, linguiça calabresa, bacon em cubos, batata palha, alface, tomate e cebola.",
            "preco": 23.90,
        },
        {
            "nome": "Double Bacon",
            "descricao": "2 carnes 100g, bacon em cubos, queijo muçarela, alface, tomate e cebola.",
            "preco": 24.90,
        },
    ],

    # ----------------------------------------------------------------
    # BATATA MALUCA — batatas fritas "montadas", com cobertura completa
    # ----------------------------------------------------------------
    "Batata Maluca": [
        {
            "nome": "Batata Média BDV",
            "descricao": "500g de batata + cheddar + molho barbecue + bacon frito.",
            "preco": 34.90,
        },
        {
            "nome": "Batata Grande BDV",
            "descricao": "Batata 1kg + cheddar + parmesão + bacon em cubos + calabresa + molhos especiais.",
            "preco": 58.90,
        },
    ],

    # ----------------------------------------------------------------
    # MINI COMBOS — combos menores, ideais para 1-2 pessoas
    # ----------------------------------------------------------------
    "Mini Combos": [
        {
            "nome": "Mini Combo 01",
            "descricao": "Batata 400g + 2 salgados à escolha.",
            "preco": 29.90,
        },
        {
            "nome": "Mini Combo Supremo",
            "descricao": "Batata 300g + anel de frango à passarinho + 250g de linguiça calabresa acebolada.",
            "preco": 33.90,
        },
        {
            "nome": "Mini Combo 02",
            "descricao": "Batata 800g + 25 salgadinhos sortidos + 2 anéis de cebola.",
            "preco": 38.90,
        },
    ],

    # ----------------------------------------------------------------
    # PORÇÕES — itens avulsos vendidos por peso/quantidade
    # ----------------------------------------------------------------
    "Porções": [
        {
            "nome": "Batata Pequena",
            "descricao": "250g.",
            "preco": 12.90,
        },
        {
            "nome": "Batata Média",
            "descricao": "500g.",
            "preco": 22.90,
        },
        {
            "nome": "Batata Grande",
            "descricao": "1kg.",
            "preco": 35.90,
        },
        {
            "nome": "Rimpim Pequeno",
            "descricao": "250g.",
            "preco": 14.90,
        },
        {
            "nome": "Rimpim Médio",
            "descricao": "500g.",
            "preco": 24.90,
        },
        {
            "nome": "Anel de Cebola",
            "descricao": "200g.",
            "preco": 23.90,
        },
        {
            "nome": "Anel de Cebola",
            "descricao": "400g.",
            "preco": 35.90,
        },
        {
            "nome": "Frango à Passarinho",
            "descricao": "1kg.",
            "preco": 29.90,
        },
        {
            "nome": "10 Nugget's Tradicional",
            "descricao": "Porção de nuggets tradicionais.",
            "preco": 16.90,
        },
        {
            "nome": "25 Salgadinhos Sortidos",
            "descricao": "Sabores: coxinha, bolinho de alho, bolinho de queijo com alho, bolinho com presunto, pizza, calabresa com catupiry e presuntinho.",
            "preco": 19.90,
        },
        {
            "nome": "50 Salgadinhos Sortidos",
            "descricao": "Sabores: coxinha, bolinho de alho, bolinho de queijo com alho, bolinho com presunto, pizza, calabresa com catupiry e presuntinho.",
            "preco": 34.90,
        },
        {
            "nome": "100 Salgadinhos Sortidos",
            "descricao": "Sabores: coxinha, bolinho de alho, bolinho de queijo com alho, bolinho com presunto, pizza, calabresa com catupiry e presuntinho.",
            "preco": 54.90,
        },
    ],

    # ----------------------------------------------------------------
    # MONTE SEU TRIO — batata + bebida em combo fixo
    # ----------------------------------------------------------------
    "Monte Seu Trio": [
        {
            "nome": "Batata P + Guaraná Natural",
            "descricao": "Batata pequena + guaraná natural.",
            "preco": 11.90,
        },
        {
            "nome": "Batata M + Guaraná Natural",
            "descricao": "Batata média + guaraná natural.",
            "preco": 12.90,
        },
        {
            "nome": "Batata P + Bebida Lata",
            "descricao": "Batata pequena + lata à escolha: guaraná, guaraná zero, coca-cola, coca-cola zero ou coca-cola zero limão.",
            "preco": 15.90,
        },
        {
            "nome": "Batata M + Bebida Lata",
            "descricao": "Batata média + lata à escolha: guaraná, guaraná zero, coca-cola, coca-cola zero ou coca-cola zero limão.",
            "preco": 16.90,
        },
    ],

    # ----------------------------------------------------------------
    # AÇAÍS — vendidos por tamanho de copo
    # ----------------------------------------------------------------
    "Açaís": [
        {
            "nome": "Açaí 400ml",
            "descricao": "Sabores: natural, banana e morango. Com calda e complemento à escolha.",
            "preco": 13.90,
        },
        {
            "nome": "Açaí 500ml",
            "descricao": "Sabores: natural, banana e morango. Com calda e complemento à escolha.",
            "preco": 14.90,
        },
        {
            "nome": "Açaí 770ml",
            "descricao": "Sabores: natural, banana e morango. Com calda e complemento à escolha.",
            "preco": 22.90,
        },
    ],

    # ----------------------------------------------------------------
    # MILK SHAKE
    # ----------------------------------------------------------------
    "Milk Shake": [
        {
            "nome": "Milk Shake 400ml",
            "descricao": "Sabores: morango ou chocolate.",
            "preco": 18.90,
        },
    ],

    # ----------------------------------------------------------------
    # BEBIDAS — latas, garrafas 1,5L e 2L
    # ----------------------------------------------------------------
    "Bebidas": [
        {
            "nome": "Guaravita Copo",
            "descricao": "280ml.",
            "preco": 2.90,
        },
        {
            "nome": "Coca-Cola Lata",
            "descricao": "310ml.",
            "preco": 7.90,
        },
        {
            "nome": "Guaraná Antarctica Lata",
            "descricao": "310ml.",
            "preco": 7.90,
        },
        {
            "nome": "Guaraná Kuat 2L",
            "descricao": "Garrafa 2 litros.",
            "preco": 10.90,
        },
        {
            "nome": "Sukita 2L",
            "descricao": "Garrafa 2 litros.",
            "preco": 10.90,
        },
        {
            "nome": "Guaraná Antarctica 1,5L",
            "descricao": "Garrafa 1,5 litros.",
            "preco": 12.90,
        },
        {
            "nome": "Coca-Cola 1,5L",
            "descricao": "Garrafa 1,5 litros.",
            "preco": 13.90,
        },
        {
            "nome": "Coca-Cola Zero 1,5L",
            "descricao": "Garrafa 1,5 litros.",
            "preco": 13.90,
        },
        {
            "nome": "Mate Natural 1,5L",
            "descricao": "Garrafa 1,5 litros.",
            "preco": 13.90,
        },
    ],

    # ----------------------------------------------------------------
    # ADICIONAIS — molhos e extras para turbinar lanches/combos
    # (junta os itens de "Turbine seu Hambúrguer" e "Turbine seu Combo"
    # do cardápio original, sem repetir os que eram iguais nos dois)
    # ----------------------------------------------------------------
    "Adicionais": [
        {
            "nome": "Molho Barbecue",
            "descricao": "Adicional para seu lanche ou combo.",
            "preco": 3.90,
        },
        {
            "nome": "Molho Billy Jack",
            "descricao": "Adicional para seu lanche ou combo.",
            "preco": 3.90,
        },
        {
            "nome": "Molho Cheddar",
            "descricao": "Adicional para seu lanche ou combo.",
            "preco": 3.90,
        },
        {
            "nome": "Molho Verde",
            "descricao": "Adicional para seu lanche ou combo.",
            "preco": 3.90,
        },
        {
            "nome": "Alho Frito",
            "descricao": "Adicional para seu lanche ou combo.",
            "preco": 4.90,
        },
        {
            "nome": "Bacon Frito",
            "descricao": "Adicional para seu lanche ou combo.",
            "preco": 4.90,
        },
        {
            "nome": "Ovo Frito",
            "descricao": "Adicional para seu lanche ou combo.",
            "preco": 5.90,
        },
        {
            "nome": "Linguiça Calabresa",
            "descricao": "Adicional para seu lanche ou combo.",
            "preco": 7.90,
        },
        {
            "nome": "Queijo Parmesão",
            "descricao": "Adicional para seu lanche ou combo.",
            "preco": 7.90,
        },
        {
            "nome": "Queijo Muçarela",
            "descricao": "Adicional para seu lanche ou combo.",
            "preco": 8.90,
        },
        {
            "nome": "Carne Extra 80g",
            "descricao": "Adicional para seu lanche.",
            "preco": 8.90,
        },
    ],
}

# Observação impressa no cardápio original do iFood: todos os lanches são
# pesados antes do preparo.


# ==========================================================================
# APP FLASK
# ==========================================================================
# A partir daqui é a parte "técnica" que faz o site funcionar.
# Normalmente você não precisa mexer aqui — só se quiser adicionar
# uma página nova (uma nova @app.route) ou mudar como os arquivos
# são organizados.

# BASE_DIR = caminho absoluto da pasta onde este arquivo (banco-de-dados.py)
# está salvo. Usamos isso para o Flask sempre achar o siteBDV.html e a
# pasta static/, não importa de que lugar do computador você rode o comando.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Cria a aplicação Flask (o "servidor" do site) e configura duas pastas:
#   - template_folder: onde fica o siteBDV.html (o HTML com {{ variáveis }})
#   - static_folder:   onde ficam arquivos "crus", como logo.png, que o
#                       navegador acessa direto pela URL (ex: /static/logo.png)
app = Flask(
    __name__,
    template_folder=BASE_DIR,                       # siteBDV.html está na mesma pasta deste arquivo
    static_folder=os.path.join(BASE_DIR, "static"),  # logo.png (e outros arquivos) ficam dentro de static/
    static_url_path="/static",                       # URL usada no navegador, ex: /static/logo.png
)


@app.route("/")
def home():
    """
    Rota principal do site (a página "/", ou seja, a home).

    Toda vez que alguém abre http://localhost:5000 no navegador, esta
    função é chamada. Ela pega o template siteBDV.html e "recheia" ele
    com os dados definidos lá em cima (nome da loja, cardápio, links de
    contato, endereço, horário...).

    Os nomes à esquerda do "=" (ex: nome_loja=) são exatamente os nomes
    das variáveis {{ nome_loja }} usadas dentro do siteBDV.html.
    Se quiser usar um dado novo no HTML, precisa adicionar aqui também.
    """
    return render_template(
        "siteBDV.html",
        nome_loja=NOME_LOJA,
        tagline=TAGLINE,
        menu=MENU,
        whatsapp_link=WHATSAPP_LINK,
        instagram_user=INSTAGRAM_USER,
        instagram_link=INSTAGRAM_LINK,
        endereco=ENDERECO,
        horario_funcionamento=HORARIO_FUNCIONAMENTO,
    )


@app.route("/api/cardapio")
def api_cardapio():
    """
    Rota extra opcional: retorna o cardápio em formato JSON puro,
    sem nenhum HTML. Útil se um dia você quiser usar esses mesmos dados
    em outro lugar (um app de celular, uma tela de totem, etc.) sem
    precisar copiar o MENU de novo.

    Para testar: rode o site e abra http://localhost:5000/api/cardapio
    """
    return jsonify(MENU)


# Este bloco só roda quando você executa "python banco-de-dados.py"
# diretamente (e não quando este arquivo é apenas importado por outro).
# app.run(debug=True) liga o servidor local e recarrega sozinho sempre
# que você salva alguma alteração no código — ótimo para ir testando.
if __name__ == "__main__":
    app.run(debug=True)