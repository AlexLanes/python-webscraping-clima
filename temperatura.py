import os # std
import json # std
import unicodedata # std
from sys import exit # std
from requests_html import HTMLSession # externo

SERVIDOR = "https://www.climatempo.com.br"

def normalizar( string: str ) -> str:
    """Remover acento, lower(), strip()"""
    nfkd = unicodedata.normalize('NFKD', string)
    ascii = nfkd.encode('ASCII', 'ignore')
    return ascii.decode("utf8").strip().lower()

def obterInput( mensagem: str = "Aguardando input...", tamanho: tuple[int, int] = (1, 1) ) -> str:
    """Obter input do usuario e validar se o range do tamanho está correto"""
    string = input(mensagem).strip()
    while len(string) < tamanho[0] or len(string) > tamanho[1]:
        print(f"Tamanho do input incorreto. Esperado o range inclusivo: {tamanho}")
        string = input(mensagem).strip()
    return string

def obterUriCidadeEstado( cidade: str, estado: str ) -> str:
    try:
        session = HTMLSession()
        response = session.get( f"{SERVIDOR}/previsao-do-tempo" )

        if response.status_code != 200:
            raise Exception("Status code diferente do esperado")
        
        cidadeEstado = normalizar( f"{cidade}, {estado}" )
        cidades = response.html.find( f"#letter-{cidade[0].upper()}", first = True ).find("a")
        for cidade in cidades:
            if normalizar(cidade.text) == cidadeEstado:
                return cidade.attrs["href"]
            
        raise Exception("URI não foi encontrada")

    except Exception as e:
        exit( f"----Erro ao obter o URI da Cidade/Estado----\n{e}\nFinalizando..." )

def obterPrevisao( uri: str ) -> dict:
    try:
        session = HTMLSession()
        response = session.get( f"{SERVIDOR}{uri}" )

        if response.status_code != 200:
            raise Exception("Status code diferente do esperado")
    
        div = response.html.find(".wrapper-chart", first = True)
        if div.attrs == None or "data-infos" not in div.attrs:
            raise Exception("Previsão não localizada no HTML")
        
        formatado = {}
        infos: list[dict] = json.loads( div.attrs["data-infos"].replace("&quot;", '"') )

        for obj in infos:
            formatado[ obj["day"] ] = {
                "diaSemana": obj["dayWeekFullMin"],
                "resumo": obj["textIcon"]["text"]["pt"],
                "temperatura": f"entre " + str(obj["temperature"]["min"]) + " e " + str(obj["temperature"]["max"]),
                "sol": "entre " + obj["sun"]["sunshine"] + " e " + obj["sun"]["sunset"],
                "chuva": "probabilidade de " + str(obj["rain"]["probability"]) + "% com precipitação de " + str(obj["rain"]["precipitation"]) + "mm",
                "arco-íris": obj["rainbow"]["text"]
            }

        return formatado

    except Exception as e:
        exit( f"----Erro ao obter a Previsão----\n{e}\nFinalizando..." )

def main() -> None:
    cidade = obterInput( "Digite o nome completo da Cidade: ", (1, 100) )
    estado = obterInput( "Digite a sigla do Estado: ", (2, 2) )
    uri15Dias = obterUriCidadeEstado(cidade, estado).replace("agora", "15-dias")
    previsao = obterPrevisao(uri15Dias)

    # Escreve no arquivo o JSON para remover os erros com unicode
    with open( "temperatura.json", "w", encoding = "utf8" ) as file:
        json.dump( previsao, file, ensure_ascii = False, indent = 4 )
    # Abre o JSON
    os.system( r"temperatura.json" )
    
if __name__ == "__main__":
    main()