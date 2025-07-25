import xml.etree.ElementTree as ET
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import os

def importar_arquivo(titulo="Selecione um arquivo .jff"):
    root = Tk()
    root.withdraw()
    root.lift()
    root.attributes("-topmost", True)
    caminho = askopenfilename(title=titulo, filetypes=[("JFLAP files", "*.jff")])
    root.destroy()
    return caminho


def carregar_automato(titulo):
    nome_arquivo = None
    while not nome_arquivo:
        print(f"\nImportando Autômato...")
        nome_arquivo = importar_arquivo(titulo)
        if not nome_arquivo:
            print("Nenhum arquivo foi selecionado.")
            retry = input("Deseja tentar novamente? (S/N): ")
            if retry.lower() != "s":
                return None

    try:
        arvore_xml = ET.parse(nome_arquivo)
        raiz_xml = arvore_xml.getroot()
        automato_xml = raiz_xml.find("automaton")
        if automato_xml is None:
            print(f"Erro: O arquivo '{nome_arquivo}' não contém a estrutura de um autômato JFLAP.")
            return None

        estados = {e.get("id"): {"nome": e.get("name"), "inicial": e.find("initial") is not None, "final": e.find("final") is not None} for e in automato_xml.findall("state")}
        transicoes = [(t.find("from").text, t.find("to").text, t.find("read").text) for t in automato_xml.findall("transition")]
        alfabeto = {s for _, _, s in transicoes if s is not None and s != "ε"}
        
        print(f"Autômato '{os.path.basename(nome_arquivo)}' carregado com sucesso.")
        return estados, transicoes, alfabeto, arvore_xml, automato_xml

    except (ET.ParseError, FileNotFoundError) as e:
        print(f"Erro ao carregar o arquivo do autômato: {e}")
        return None

def salvar_automato(estados, transicoes):

    raiz_xml = ET.Element("structure")
    ET.SubElement(raiz_xml, "type").text = "fa"
    automato_xml = ET.SubElement(raiz_xml, "automaton")

    for id_estado, info_estado in estados.items():
        elemento_estado_xml = ET.SubElement(
            automato_xml, "state", id=id_estado, name=info_estado["nome"])
        ET.SubElement(elemento_estado_xml, "x").text = "0.0"
        ET.SubElement(elemento_estado_xml, "y").text = "0.0"
        if info_estado.get("inicial"):
            ET.SubElement(elemento_estado_xml, "initial")
        if info_estado.get("final"):
            ET.SubElement(elemento_estado_xml, "final")

    for de, para, simbolo in transicoes:
        elemento_transicao_xml = ET.SubElement(automato_xml, "transition")
        ET.SubElement(elemento_transicao_xml, "from").text = de
        ET.SubElement(elemento_transicao_xml, "to").text = para
        simbolo_lido = simbolo if simbolo is not None else ""
        ET.SubElement(elemento_transicao_xml, "read").text = "" if simbolo_lido == "ε" else simbolo_lido

    try:
        nome_saida = input("Digite o nome para salvar arquivo: ") or "automato.jff"
        if not nome_saida.endswith(".jff"):
            nome_saida += ".jff"
        arvore_xml = ET.ElementTree(raiz_xml)
        arvore_xml.write(nome_saida, encoding="utf-8", xml_declaration=True)
        print(f"\nArquivo '{nome_saida}' salvo com sucesso.")
    except Exception as e:
        print(f"\nErro ao salvar o arquivo '{nome_saida}': {e}")

def completar_automato(estados, transicoes, alfabeto, arvore_xml, automato_xml):
    transicoes_existentes = {(de, simbolo) for de, _, simbolo in transicoes if simbolo is not None and simbolo != 'ε'}

    ids_numericos = [int(i) for i in estados.keys() if i.isdigit()]
    id_consumidor = str(max(ids_numericos) + 1 if ids_numericos else len(estados))
    nome_consumidor = "q_erro"
    
    estados[id_consumidor] = {"nome": nome_consumidor,"inicial": False,"final": False}
    novas_transicoes = []
    
    for simbolo in alfabeto:
        novas_transicoes.append((id_consumidor, id_consumidor, simbolo))

    for id_estado in list(estados.keys()):
        if id_estado == id_consumidor:
            continue
        for simbolo in alfabeto:
            if (id_estado, simbolo) not in transicoes_existentes:
                novas_transicoes.append((id_estado, id_consumidor, simbolo))

    transicoes.extend(novas_transicoes)
    
    return estados, transicoes

def remover_estados_inuteis(estados, transicoes):

    id_estado_inicial = next((id_e for id_e, info in estados.items() if info.get("inicial")), None)
    
    if id_estado_inicial is None:
        print("Aviso: Nenhum estado inicial encontrado.")
        return estados, transicoes

    estados_alcancaveis = set()
    fila_para_visitar = [id_estado_inicial]
    estados_alcancaveis.add(id_estado_inicial)

    while fila_para_visitar:
        id_atual = fila_para_visitar.pop(0)
        for de, para, simbolo in transicoes:
            if de == id_atual and para not in estados_alcancaveis:
                estados_alcancaveis.add(para)
                fila_para_visitar.append(para)
    
    estados_originais_cont = len(estados)
    novos_estados = {id_e: info for id_e, info in estados.items() if id_e in estados_alcancaveis}
    novas_transicoes = [(de, para, simbolo) for de, para, simbolo in transicoes if de in estados_alcancaveis and para in estados_alcancaveis]
    
    return novos_estados, novas_transicoes

def aplicar_estrela(estados, transicoes, arvore_xml, automato_xml):
    novos_ids_int = []
    for id_estado in estados.keys():
        if id_estado.isdigit():
            novos_ids_int.append(int(id_estado))
    
    proximo_id = max(novos_ids_int) + 1 if novos_ids_int else 0
    
    novo_id_inicial = str(proximo_id)
    nome_novo_inicial = f"q{novo_id_inicial}"

    novo_id_final = str(proximo_id + 1)
    nome_novo_final = f"q{novo_id_final}"

    estado_inicial_antigo = None
    estados_finais_antigos = []

    for id_estado, info_estado in estados.items():
        if info_estado.get("inicial"):
            estado_inicial_antigo = id_estado
            estados[id_estado]["inicial"] = False
        if info_estado.get("final"):
            estados_finais_antigos.append(id_estado)
            estados[id_estado]["final"] = False

    if estado_inicial_antigo is None:
        print("Erro: Autômato não possui estado inicial definido. Não é possível aplicar a estrela.")
        return estados, transicoes

    estados[novo_id_inicial] = {"nome": nome_novo_inicial,"inicial": True,"final": False}
    estados[novo_id_final] = {"nome": nome_novo_final,"inicial": False,"final": True}

    transicoes.append((novo_id_inicial, estado_inicial_antigo, "ε"))
    transicoes.append((novo_id_inicial, novo_id_final, "ε"))

    for id_final_antigo in estados_finais_antigos:
        transicoes.append((id_final_antigo, novo_id_final, "ε"))
        transicoes.append((id_final_antigo, estado_inicial_antigo, "ε"))

    for element in list(automato_xml):
        if element.tag in ["state", "transition"]:
            automato_xml.remove(element)

    for id_estado, info_estado in estados.items():
        elemento_estado_xml = ET.SubElement(automato_xml, "state", id=id_estado, name=info_estado["nome"])
        
        ET.SubElement(elemento_estado_xml, "x").text = "0" 
        ET.SubElement(elemento_estado_xml, "y").text = "0"
        
        if info_estado.get("inicial"):
            ET.SubElement(elemento_estado_xml, "initial")
        if info_estado.get("final"):
            ET.SubElement(elemento_estado_xml, "final")

    for de_estado, para_estado, simbolo in transicoes:
        elemento_transicao_xml = ET.SubElement(automato_xml, "transition")
        ET.SubElement(elemento_transicao_xml, "from").text = de_estado
        ET.SubElement(elemento_transicao_xml, "to").text = para_estado
        ET.SubElement(elemento_transicao_xml, "read").text = "" if simbolo == "ε" else simbolo

    return estados, transicoes

def eh_completo(estados, transicoes, alfabeto):
    transicoes_por_estado_simbolo = {}
    for de_estado, _, simbolo in transicoes:
        if simbolo is None or simbolo == 'ε': return False
        if (de_estado, simbolo) in transicoes_por_estado_simbolo: return False
        transicoes_por_estado_simbolo[(de_estado, simbolo)] = True

    for id_estado in estados.keys():
        for simbolo in alfabeto:
            if (id_estado, simbolo) not in transicoes_por_estado_simbolo:
                return False
    return True

def aplicar_complemento(estados, transicoes, arvore_xml, automato_xml, alfabeto):

    if not eh_completo(estados, transicoes, alfabeto):
        estados, transicoes = completar_automato(estados, transicoes, alfabeto, arvore_xml, automato_xml)

    for id_estado in estados:
        estados[id_estado]["final"] = not estados[id_estado]["final"]

    for elemento in automato_xml.findall("state") + automato_xml.findall("transition"):
        if elemento in automato_xml:
            automato_xml.remove(elemento)

    for id_estado, info_estado in estados.items():
        elemento_estado_xml = ET.SubElement(automato_xml, "state", id=id_estado, name=info_estado["nome"])
        if info_estado.get("inicial"):
            ET.SubElement(elemento_estado_xml, "initial")
        if info_estado.get("final"):
            ET.SubElement(elemento_estado_xml, "final")
        ET.SubElement(elemento_estado_xml, "x").text = "0"
        ET.SubElement(elemento_estado_xml, "y").text = "0"

    for de_estado, para_estado, simbolo in transicoes:
        elemento_transicao_xml = ET.SubElement(automato_xml, "transition")
        ET.SubElement(elemento_transicao_xml, "from").text = de_estado
        ET.SubElement(elemento_transicao_xml, "to").text = para_estado
        ET.SubElement(elemento_transicao_xml, "read").text = "" if simbolo == "ε" else simbolo

    return estados, transicoes

def aplicar_diferenca_simetrica(estados1, transicoes1, alfabeto1, arvore_xml1, automato_xml1, estados2, transicoes2, alfabeto2, arvore_xml2, automato_xml2):

    alfabeto_uniao = alfabeto1.union(alfabeto2)

    if not eh_completo(estados1, transicoes1, alfabeto_uniao):
        estados1, transicoes1 = completar_automato(estados1, transicoes1, alfabeto_uniao, arvore_xml1, automato_xml1)

    if not eh_completo(estados2, transicoes2, alfabeto_uniao):
        estados2, transicoes2 = completar_automato(estados2, transicoes2, alfabeto_uniao, arvore_xml2, automato_xml2)
    
    novos_estados = {}
    novas_transicoes = []
    mapa_originais_para_novo_id = {}
    contador_novo_estado = 0

    for id1, info1 in estados1.items():
        for id2, info2 in estados2.items():
            novo_id = str(contador_novo_estado)
            novo_nome_combinado = f"({info1['nome']},{info2['nome']})"
            mapa_originais_para_novo_id[(id1, id2)] = novo_id
            eh_final = (info1["final"] and not info2["final"]) or (not info1["final"] and info2["final"])
            novos_estados[novo_id] = {"nome": novo_nome_combinado,"inicial": info1["inicial"] and info2["inicial"],"final": eh_final}
            contador_novo_estado += 1

    mapa_transicoes1 = {(f, s): t for f, t, s in transicoes1}
    mapa_transicoes2 = {(f, s): t for f, t, s in transicoes2}

    for (id1, id2), id_novo_origem in mapa_originais_para_novo_id.items():
        for simbolo in alfabeto_uniao:
            id_destino1 = mapa_transicoes1.get((id1, simbolo))
            id_destino2 = mapa_transicoes2.get((id2, simbolo))
            if id_destino1 is not None and id_destino2 is not None:
                id_novo_destino = mapa_originais_para_novo_id.get((id_destino1, id_destino2))
                if id_novo_destino is not None:
                    novas_transicoes.append((id_novo_origem, id_novo_destino, simbolo))

    return novos_estados, novas_transicoes


def main():
    entrada = "s"
    while entrada == "s" or entrada == "S":

        print("\nEscolha uma operação:")
        print("0 - Voltar")
        print("1 - Operação ESTRELA (Fecho de Kleene)")
        print("2 - Operação COMPLEMENTO")
        print("3 - Operação DIFERENÇA SIMÉTRICA (requer 2 autômatos)")
        entrada_usuario = input("Digite sua escolha: ")

        if entrada_usuario == "0":
            print("Saindo...")
            return

        dados_automato1 = carregar_automato("Selecione o arquivo do Autômato")
        if dados_automato1 is None:
            break

        estados1, transicoes1, alfabeto1, arvore_xml1, automato_xml1 = dados_automato1

        if entrada_usuario == "1":
            estados1, transicoes1 = aplicar_estrela(estados1, transicoes1, arvore_xml1, automato_xml1)
            salvar_automato(estados1, transicoes1)
        elif entrada_usuario == "2":
            estados1, transicoes1 = aplicar_complemento(estados1, transicoes1, arvore_xml1, automato_xml1, alfabeto1)
            salvar_automato(estados1, transicoes1)
        elif entrada_usuario == "3":
            dados_automato2 = carregar_automato("Selecione o arquivo do Autômato 2")
            if dados_automato2 is None:
                print("Operação de diferença simétrica cancelada.")
                continue

            estados2, transicoes2, alfabeto2, arvore_xml2, automato_xml2 = dados_automato2

            novos_estados, novas_transicoes = aplicar_diferenca_simetrica(estados1, transicoes1, alfabeto1, arvore_xml1, automato_xml1,estados2, transicoes2, alfabeto2, arvore_xml2, automato_xml2)
            
            if novos_estados:
                estados_limpos, transicoes_limpas = remover_estados_inuteis(novos_estados, novas_transicoes)
                salvar_automato(estados_limpos, transicoes_limpas)
        else:
            print("Opção inválida.")

        entrada = input("\nDeseja fazer outra operação? (S/N): ")

    print("Fim do programa.")

if __name__ == "__main__":
    main()
