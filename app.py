from dash_bootstrap_templates import ThemeChangerAIO, template_from_url
from dash import Dash, html, dcc, Input, Output, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


# Importação do arquivo csv
supermarket_df = pd.read_csv("assets/data/supermarket_sales - Sheet1.csv")


# Inicio do tratamento de dados do Dataframe
supermarket_df = supermarket_df.drop(["cogs", "gross margin percentage", "gross income"], axis=1)
supermarket_df['Date'] = pd.to_datetime(supermarket_df['Date'])

ids = [
    search
    for search in supermarket_df['Invoice ID'].str.findall(r'[0-9]{3}[-][0-9]{2}[-][0-9]{2}[4|5]7')
    if len(search) > 0
]

for search in ids:
    search = search[0]
    string_id = list(search)
    string_id[-2], string_id[-1] = "0", "0"
    string_id = "".join(string_id)
    supermarket_df.loc[supermarket_df['Invoice ID'] == search, 'Invoice ID'] = string_id
# Fim do tratamento de dados do Dataframe


# Inicio da criação de amostras de Dataframe
# 1 - Utilizado na tabela de produtos
rating = supermarket_df.groupby('Product line')['Rating'].mean().reset_index().sort_values(by='Rating', ascending=False)
rating['Rating'] = rating['Rating'].map('{:0.2f}'.format)

# 2 - Utilizado no indicator de correlação de Pearson
price_quantity = supermarket_df[['Unit price', 'Quantity']].copy(deep=True)
corr_matrix = price_quantity.corr(method='pearson')
pearson_corr = corr_matrix.loc['Quantity', 'Unit price']

# 3 - Utilizado no gráfico de barras de perfil de cliente.
client_prof = supermarket_df.groupby(['City', 'Customer type', 'Gender'])['Total'].sum().reset_index()

# 4 - Utilizado no gráfico de barras de quantidade de vendas na semana.
sample = supermarket_df[['Product line', 'Quantity', 'Unit price', 'Date']].copy(deep=True)
sample['Day of Week'] = sample['Date'].dt.day_name()
week_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
sample['Day of Week'] = pd.Categorical(sample['Day of Week'], categories=week_order, ordered=True)
week_sales = sample.groupby('Day of Week')['Quantity'].sum().reset_index()

# 5 - Utilizando no gráfico do relatório de vendas
month_sales = supermarket_df[['Date', 'Total']].copy(deep=True)
month_sales = month_sales.sort_values(by='Date')
month_sales['Month'] = month_sales['Date'].dt.month_name()
month_report = month_sales.groupby('Month')['Total'].sum().reset_index()
# Fim da criação de amostras de Dataframe


# Inicio da construção do CSS do dashboard
class_title = 'text-center my-2'

# Selecionando os temas que vão ser utilizados no ThemeChangerAIO
available_themes = [
    {"label": "Journal", "value": dbc.themes.JOURNAL},
    {"label": "Cyborg", "value": dbc.themes.CYBORG},
    {"label": "Superhero", "value": dbc.themes.SUPERHERO},
    {"label": "Vapor", "value": dbc.themes.VAPOR},
]
# Fim da construção do CSS do dashboard


# Inicio da construção da interface do dashboard
app.layout = dbc.Container([

    # Utilizando o ThemeChangerAIO para mudança de tema
    dbc.Row(ThemeChangerAIO(aio_id="theme", radio_props={"value": dbc.themes.CYBORG, "options": available_themes})),

    dbc.Row([html.H1(children='Dash App', className=class_title)]),

    dbc.Row([
        dbc.Col([
            html.H4(children='Product Line Ratings', className=class_title),
            dcc.Graph(id="pie_chart"),
            html.H4(children='average product line reviews', className=class_title),
            dash_table.DataTable(
                id='rating_table',
                data=rating.to_dict('records'),
                columns=[{"name": i, "id": i} for i in rating.columns]
            )
        ]),
        dbc.Col([
            html.H4(children='Scatter Plot', className=class_title),
            dcc.Graph(id='scatter_plot'),
            html.H4(children='Pearson Correlation Result', className=class_title),
            dcc.Graph(id='indicator')
        ])
    ]),

    dbc.Row([
        html.H4(children="Monthly Sales Report", className=class_title),
        dcc.Graph(id='month_report')
    ]),

    dbc.Row([
        dbc.Col([
            html.H4(children="Client Profile", className=class_title),
            dcc.Graph(id='client_bar')
        ]),
        dbc.Col([
            html.H4(children="Sales By Day Of The Week", className=class_title),
            dcc.Graph(id='week_bar')
        ])
    ])

])
# Fim da construção da interface do dashboard


# Inicio da construção de callbacks do dashboard
@app.callback(
    Output("pie_chart", "figure"),
    Output('scatter_plot', 'figure'),
    Output('indicator', 'figure'),
    Output('month_report', 'figure'),
    Input(ThemeChangerAIO.ids.radio('theme'), 'value')
)
def update_themes(theme):
    """
        Explicação 1º callback:
        Este primeiro callback é destinado à mudança de temas através do ThemeChangerAIO.
        Há 4 gráficos que serão os inputs: 1 gráfico de pizza, 1 gráfico de dispersão, 1
        indicador de correlação de Pearson e 1 gráfico de linhas. Cada gráfico tem seu
        tema atualizado conforme o tema selecionado pelo usuário no botão do
        ThemeChangerAIO.

        Os 4 gráficos usam amostras do dataframe coletadas nas primeiras seções de
        código. Cada amostra é individualmente utilizada para construir um gráfico. Após
        a construção do gráfico, a função retorna os gráficos formatados para o parâmetro
        'figure' de cada Output.
    """
    pie = px.pie(supermarket_df, values='Rating', names='Product line')
    pie.update_layout(template=template_from_url(theme), margin=dict(l=0, r=0, t=10, b=10))

    scatter = px.scatter(supermarket_df, x=supermarket_df['Unit price'], y=supermarket_df['Quantity'])
    scatter.update_layout(template=template_from_url(theme), margin=dict(l=0, r=0, t=5, b=10))

    indicator = go.Figure(go.Indicator(
        mode="number",
        value=pearson_corr,
        number={'font': {'size': 50}},
        domain={'x': [0, 1], 'y': [0, 1]})
    )
    indicator.update_layout(template=template_from_url(theme), height=210)

    report = go.Figure()
    report.add_trace(go.Scatter(
        x=month_report['Month'],
        y=month_report['Total'],
        mode='lines',
        fill='tonexty',
        fillcolor='#9ac692',
        line={'color': '#53bf3f'})
    )
    report.update_layout(
        template=template_from_url(theme),
        margin=dict(l=0, r=0, t=5, b=10)
    )

    return pie, scatter, indicator, report


@app.callback(
    Output('client_bar', 'figure'),
    Output('week_bar', 'figure'),
    Input(ThemeChangerAIO.ids.radio('theme'), 'value')
)
def update_bar(theme):
    """
        Explicação do 2º Callback:
        Este segundo callback destina-se à mudança de temas através do ThemeChangerAIO.
        Especificamente, este callback modifica apenas os gráficos de barras. Os gráficos
        de barras são exibidos lado a lado no dashboard. O processo de modificação é
        semelhante ao processo descrito no primeiro callback. São utilizadas amostras do
        DataFrame original, os gráficos são montados individualmente e, em seguida,
        atribuídos ao atributo 'figure' dos respectivos Outputs.
    """
    client_bar = px.bar(client_prof, x=client_prof.index, y='Total', color='Total', color_continuous_scale='plasma')
    client_bar.update_layout(
        template=template_from_url(theme),
        xaxis=dict(
            tickmode='array',
            tickvals=client_prof.index,
            ticktext=[f"{row['City']}-{row['Customer type']}-{row['Gender']}" for index, row in
                      client_prof.iterrows()]
        ),
        margin=dict(l=0, r=0, t=10, b=10)
    )

    week_bar = px.bar(week_sales, x='Day of Week', y='Quantity', color='Quantity', color_continuous_scale='bluered')
    week_bar.update_layout(template=template_from_url(theme), margin=dict(l=0, r=0, t=10, b=10))

    return client_bar, week_bar


@app.callback(
    Output('rating_table', 'style_data'),
    Output('rating_table', 'style_header'),
    Input(ThemeChangerAIO.ids.radio('theme'), 'value')
)
def update_table_colors(theme):
    """
        Explicação 3º callback:
        Este segundo callback é destinado à mudança de temas através do ThemeChangerAIO.
        Infelizmente, o dash DataTable não pode ser alterado diretamente pelo ThemeChangerAIO.
        Alternativamente, podemos mudar o CSS da tabela e de seu cabeçalho comparando o tema
        selecionado com os temas disponíveis do DBC. Através deste método, conseguimos mudar
        as cores de fundo e as cores do texto da tabela.
    """
    if theme == dbc.themes.JOURNAL:
        header_style = {'backgroundColor': '#dcd9d9', 'color': 'black', 'textAlign': 'center'}
        cell_style = {'backgroundColor': 'white', 'color': 'black', 'textAlign': 'center'}

    elif theme == dbc.themes.CYBORG:
        header_style = {'backgroundColor': '#282828', 'color': 'white', 'textAlign': 'center'}
        cell_style = {'backgroundColor': 'black', 'color': 'white', 'textAlign': 'center'}

    elif theme == dbc.themes.SUPERHERO:
        header_style = {'backgroundColor': '#505c6c', 'color': 'white', 'textAlign': 'center'}
        cell_style = {'backgroundColor': '#75859c', 'color': 'white', 'textAlign': 'center'}

    else:
        header_style = {
            'backgroundColor': '#200c34',
            'color': '#38fce4',
            'textAlign': 'center',
            'border': '1px solid #38fce4'
        }

        cell_style = {
            'backgroundColor': '#200c34',
            'color': '#38fce4',
            'textAlign': 'center',
            'border': '1px solid #38fce4'
        }

    return cell_style, header_style


if __name__ == '__main__':
    app.run(debug=True)
