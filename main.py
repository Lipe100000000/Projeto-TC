import xml.etree.ElementTree as ET
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import os

def selecionar_arquivo(titulo="Selecione um arquivo .jff"):
    Tk().withdraw()
    return askopenfilename(title=titulo, filetypes=[("JFLAP files", "*.jff")])

def completar_automato(estados, transicoes, alfabeto, arvore_xml, automato_xml, nome_saida="completo.jff"):
    print("\nIniciando o processo para completar o autômato...")

    transicoes_existentes = {(de, simbolo) for de, _, simbolo in transicoes if simbolo != 'ε'}

    ids_numericos = [int(i) for i in estados.keys() if i.isdigit()]
    id_consumidor = str(max(ids_numericos) + 1 if ids_numericos else 0)
    nome_consumidor = "q_erro"
    
    estados[id_consumidor] = {
        "nome": nome_consumidor,
        "inicial": False,
        "final": False
    }

    novas_transicoes = []
    for id_estado in list(estados.keys()):
        for simbolo in alfabeto:
            if (id_estado, simbolo) not in transicoes_existentes:
                novas_transicoes.append((id_estado, id_consumidor, simbolo))
                print(f"Adicionando transição faltante: ({estados[id_estado]['nome']}, {simbolo}) -> {nome_consumidor}")

    transicoes.extend(novas_transicoes)

    for elemento in automato_xml.findall("state") + automato_xml.findall("transition"):
        automato_xml.remove(elemento)

    for id_estado, info_estado in estados.items():
        elemento_estado_xml = ET.SubElement(
            automato_xml, "state", id=id_estado, name=info_estado["nome"])
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
        ET.SubElement(elemento_transicao_xml,
                      "read").text = "" if simbolo == "ε" else simbolo

    arvore_xml.write(nome_saida, encoding="utf-8", xml_declaration=True)
    print(f"\nArquivo '{nome_saida}' salvo com sucesso.")

    return estados, transicoes

def aplicar_estrela(estados, transicoes, arvore_xml, automato_xml, nome_saida="estrela_aplicada.jff"):
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

    estados[novo_id_inicial] = {
        "nome": nome_novo_inicial,
        "inicial": True,
        "final": False
    }

    estados[novo_id_final] = {
        "nome": nome_novo_final,
        "inicial": False,
        "final": True
    }

    transicoes.append((novo_id_inicial, estado_inicial_antigo, "ε"))
    transicoes.append((novo_id_inicial, novo_id_final, "ε"))

    for id_final_antigo in estados_finais_antigos:
        transicoes.append((id_final_antigo, novo_id_final, "ε"))
        transicoes.append((id_final_antigo, estado_inicial_antigo, "ε"))

    for element in list(automato_xml):
        if element.tag in ["state", "transition"]:
            automato_xml.remove(element)

    for id_estado, info_estado in estados.items():
        elemento_estado_xml = ET.SubElement(
            automato_xml, "state", id=id_estado, name=info_estado["nome"])
        
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

    try:
        arvore_xml.write(nome_saida, encoding="utf-8", xml_declaration=True)
        print(f"\nArquivo '{nome_saida}' salvo com sucesso.")
    except Exception as e:
        print(f"\nErro ao salvar o arquivo '{nome_saida}': {e}")

    return estados, transicoes
def eh_completo(estados, transicoes, alfabeto):
    for _, _, simbolo in transicoes:
        if simbolo == "ε":
            print("Erro: O autômato possui transições epsilon. Não é um AFD completo.")
            return False

    transicoes_por_estado_simbolo = {}
    for de_estado, _, simbolo in transicoes:
        if (de_estado, simbolo) in transicoes_por_estado_simbolo:
            print(
                f"Erro: O autômato possui múltiplas transições para o estado {estados[de_estado]['nome']} com o símbolo '{simbolo}'. Não é um AFD completo.")
            return False
        transicoes_por_estado_simbolo[(de_estado, simbolo)] = True

    for id_estado in estados.keys():
        for simbolo in alfabeto:
            if (id_estado, simbolo) not in transicoes_por_estado_simbolo:
                print(
                    f"Erro: O estado {estados[id_estado]['nome']} não possui transição para o símbolo '{simbolo}'. O autômato não é completo.")
                return False
    return True

def aplicar_complemento(estados, transicoes, arvore_xml, automato_xml, alfabeto, nome_saida="complemento_aplicado.jff"):
    """
    Aplica a operação de complemento em um autômato.
    Se o autômato não for completo, ele o completa antes de inverter os estados.
    """
    print("\n--- Iniciando Operação de Complemento ---")

    if not eh_completo(estados, transicoes, alfabeto):
        print("O autômato não é completo. Iniciando o processo para completá-lo...")
        
        estados, transicoes = completar_automato(
            estados,
            transicoes,
            alfabeto,
            arvore_xml,
            automato_xml,
            nome_saida="automato_completo_temp.jff" 
        )
        print("Autômato completado. Continuando com a operação de complemento...")

    print("Invertendo estados finais e não-finais...")
    for id_estado in estados:
        estados[id_estado]["final"] = not estados[id_estado]["final"]

    print("O estado 'q_erro' agora é um estado final.")

    print(f"Salvando o resultado final do complemento em '{nome_saida}'...")

    for elemento in automato_xml.findall("state") + automato_xml.findall("transition"):
        if elemento in automato_xml:
            automato_xml.remove(elemento)

    for id_estado, info_estado in estados.items():
        elemento_estado_xml = ET.SubElement(
            automato_xml, "state", id=id_estado, name=info_estado["nome"])
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
        ET.SubElement(elemento_transicao_xml,
                      "read").text = "" if simbolo == "ε" else simbolo

    arvore_xml.write(nome_saida, encoding="utf-8", xml_declaration=True)
    print(f"\nArquivo de complemento '{nome_saida}' salvo com sucesso.")

    return estados, transicoes


def eh_completo(estados, transicoes, alfabeto):

    transicoes_por_estado_simbolo = {}
    for de_estado, _, simbolo in transicoes:
        if simbolo == 'ε': return False 
        if (de_estado, simbolo) in transicoes_por_estado_simbolo:
            return False 
        transicoes_por_estado_simbolo[(de_estado, simbolo)] = True

    for id_estado in estados.keys():
        for simbolo in alfabeto:
            if (id_estado, simbolo) not in transicoes_por_estado_simbolo:
                return False 
    return True

def aplicar_diferenca_simetrica(estados1, transicoes1, alfabeto1, estados2, transicoes2, alfabeto2, nome_saida="diferenca_simetrica_aplicada.jff"):
    print("Verificando o Autômato 1...")
    if not eh_completo(estados1, transicoes1, alfabeto1):
        print("Erro: O Autômato 1 não é um AFD completo. Não é possível aplicar a diferença simétrica.")
        return None, None

    print("Verificando o Autômato 2...")
    if not eh_completo(estados2, transicoes2, alfabeto2):
        print("Erro: O Autômato 2 não é um AFD completo. Não é possível aplicar a diferença simétrica.")
        return None, None

    alfabeto_resultado = alfabeto1.union(alfabeto2)

    novos_estados = {}
    novas_transicoes = []
    id_estado_inicial_resultado = None
    contador_novo_estado = 0

    mapa_ids1_para_nomes = {id_e: estados1[id_e]["nome"] for id_e in estados1}
    mapa_ids2_para_nomes = {id_e: estados2[id_e]["nome"] for id_e in estados2}

    for id1, info1 in estados1.items():
        for id2, info2 in estados2.items():
            novo_id = str(contador_novo_estado)
            novo_nome_combinado = f"({info1['nome']},{info2['nome']})"

            novos_estados[novo_id] = {
                "nome": novo_nome_combinado,
                "inicial": False,
                "final": False
            }

            if info1["inicial"] and info2["inicial"]:
                novos_estados[novo_id]["inicial"] = True
                id_estado_inicial_resultado = novo_id

            if (info1["final"] and not info2["final"]) or (not info1["final"] and info2["final"]):
                novos_estados[novo_id]["final"] = True

            contador_novo_estado += 1

    if id_estado_inicial_resultado is None:
        print("Erro: Não foi possível determinar o estado inicial do autômato resultante. Verifique se ambos os autômato de entrada têm estados iniciais.")
        return None, None

    tabela_busca_id_estado = {}
    for novo_id_s, info_novo_s in novos_estados.items():
        partes_nome = info_novo_s["nome"][1:-1].split(',')
        nome_original1 = partes_nome[0]
        nome_original2 = partes_nome[1]

        id1_original = None
        for id_e, info_e in estados1.items():
            if info_e["nome"] == nome_original1:
                id1_original = id_e
                break
        id2_original = None
        for id_e, info_e in estados2.items():
            if info_e["nome"] == nome_original2:
                id2_original = id_e
                break

        if id1_original is not None and id2_original is not None:
            tabela_busca_id_estado[(id1_original, id2_original)] = novo_id_s
        else:
            print(
                f"Aviso: Não foi possível mapear o nome combinado {info_novo_s['nome']} de volta aos IDs originais.")

    for id_atual_novo, info_atual_novo in novos_estados.items():
        partes_nome = info_atual_novo["nome"][1:-1].split(',')
        nome_original1 = partes_nome[0]
        nome_original2 = partes_nome[1]

        id_atual1_original = None
        for id_e, info_e in estados1.items():
            if info_e["nome"] == nome_original1:
                id_atual1_original = id_e
                break
        id_atual2_original = None
        for id_e, info_e in estados2.items():
            if info_e["nome"] == nome_original2:
                id_atual2_original = id_e
                break

        if id_atual1_original is None or id_atual2_original is None:
            continue

        mapa_transicoes1 = {}
        for f, t, s in transicoes1:
            if f == id_atual1_original:
                mapa_transicoes1[s] = t

        mapa_transicoes2 = {}
        for f, t, s in transicoes2:
            if f == id_atual2_original:
                mapa_transicoes2[s] = t

        for simbolo_alfabeto in alfabeto_resultado:
            id_destino1 = mapa_transicoes1.get(simbolo_alfabeto)
            id_destino2 = mapa_transicoes2.get(simbolo_alfabeto)

            if id_destino1 is not None and id_destino2 is not None:
                id_destino_novo = tabela_busca_id_estado.get(
                    (id_destino1, id_destino2))
                if id_destino_novo is not None:
                    novas_transicoes.append(
                        (id_atual_novo, id_destino_novo, simbolo_alfabeto))
                else:
                    print(
                        f"Aviso: Não encontrou o novo estado de destino para ({id_destino1},{id_destino2}) com símbolo {simbolo_alfabeto}. Isso pode indicar um problema na construção do autômato produto.")
            else:
                print(
                    f"Aviso: Autômato incompleto ou símbolo ausente para ({id_atual1_original},{id_atual2_original}) no símbolo '{simbolo_alfabeto}'.")

    raiz_xml = ET.Element("structure")
    ET.SubElement(raiz_xml, "type").text = "fa"
    elemento_automato_xml = ET.SubElement(raiz_xml, "automaton")

    for id_estado, info_estado in novos_estados.items():
        elemento_estado_xml = ET.SubElement(
            elemento_automato_xml, "state", id=id_estado, name=info_estado["nome"])
        ET.SubElement(elemento_estado_xml, "x").text = "0"
        ET.SubElement(elemento_estado_xml, "y").text = "0"
        if info_estado["inicial"]:
            ET.SubElement(elemento_estado_xml, "initial")
        if info_estado["final"]:
            ET.SubElement(elemento_estado_xml, "final")

    for de_estado, para_estado, simbolo in novas_transicoes:
        elemento_transicao_xml = ET.SubElement(
            elemento_automato_xml, "transition")
        ET.SubElement(elemento_transicao_xml, "from").text = de_estado
        ET.SubElement(elemento_transicao_xml, "to").text = para_estado
        ET.SubElement(elemento_transicao_xml,
                      "read").text = "" if simbolo == "ε" else simbolo

    nova_arvore_xml = ET.ElementTree(raiz_xml)
    nova_arvore_xml.write(nome_saida, encoding="utf-8", xml_declaration=True)
    print(f"\nArquivo '{nome_saida}' salvo com sucesso.")

    return novos_estados, novas_transicoes


def main():
    entrada = "s"
    while entrada.lower() == "s":
        nome_arquivo1 = None
        while not nome_arquivo1:
            print("\n--- Carregando Autômato 1 ---")
            nome_arquivo1 = selecionar_arquivo("Selecione o arquivo do Autômato 1")
            print(f"DEBUG: Caminho do arquivo selecionado (Autômato 1): '{nome_arquivo1}'")
            if not nome_arquivo1:
                print("Nenhum arquivo foi selecionado para o Autômato 1.")
                retry_automaton1 = input("Deseja tentar novamente selecionar o Autômato 1? (S/N): ")
                if retry_automaton1.lower() != "s":
                    entrada = "n"
                    break
        if entrada.lower() == "n":
            break

        if nome_arquivo1 and not os.path.exists(nome_arquivo1):
            print(f"Erro: O arquivo '{nome_arquivo1}' não foi encontrado. Por favor, selecione um arquivo válido.")
            continue

        try:
            arvore_xml1 = ET.parse(nome_arquivo1)
            raiz_xml1 = arvore_xml1.getroot()
            automato_xml1 = raiz_xml1.find("automaton")
            if automato_xml1 is None:
                print(f"Erro: O arquivo '{nome_arquivo1}' não contém uma tag 'automaton' válida. Por favor, verifique o formato do arquivo JFLAP.")
                continue
        except ET.ParseError as e:
            print(f"Erro ao analisar o arquivo XML do Autômato 1: {e}. Certifique-se de que é um arquivo JFLAP válido.")
            continue

        estados1 = {}
        transicoes1 = []

        for estado_elemento in automato_xml1.findall("state"):
            id_estado = estado_elemento.get("id")
            nome_estado = estado_elemento.get("name")
            estados1[id_estado] = {
                "nome": nome_estado,
                "inicial": estado_elemento.find("initial") is not None,
                "final": estado_elemento.find("final") is not None
            }

        for transicao_elemento in automato_xml1.findall("transition"):
            de_estado = transicao_elemento.find("from").text
            para_estado = transicao_elemento.find("to").text
            leitura = transicao_elemento.find(
                "read").text if transicao_elemento.find("read") is not None else "ε"
            transicoes1.append((de_estado, para_estado, leitura))

        alfabeto1 = set()
        for _, _, simbolo in transicoes1:
            if simbolo != "ε":
                alfabeto1.add(simbolo)

        print("\nEscolha uma operação para o Autômato 1:")
        print("1 - Operação ESTRELA (Kleene Star)")
        print("2 - Operação COMPLEMENTO")
        print("3 - Operação DIFERENÇA SIMÉTRICA (requer 2 autômatos)")
        print("Qualquer outra tecla para sair")
        entrada_usuario = input("Digite sua escolha: ")

        if entrada_usuario == "1":
            estados1, transicoes1 = aplicar_estrela(
                estados1, transicoes1, arvore_xml1, automato_xml1)
        elif entrada_usuario == "2":
            estados1, transicoes1 = aplicar_complemento(
                estados1, transicoes1, arvore_xml1, automato_xml1, alfabeto1)
        elif entrada_usuario == "3":
            nome_arquivo2 = None
            while not nome_arquivo2:
                print("\n--- Carregando Autômato 2 para Diferença Simétrica ---")
                nome_arquivo2 = selecionar_arquivo("Selecione o arquivo do Autômato 2")
                print(f"DEBUG: Caminho do arquivo selecionado (Autômato 2): '{nome_arquivo2}'")
                if not nome_arquivo2:
                    print("Nenhum arquivo foi selecionado para o Autômato 2.")
                    retry_automaton2 = input("Deseja tentar novamente selecionar o Autômato 2 ou cancelar a operação? (S/N para tentar novamente, C para cancelar): ")
                    if retry_automaton2.lower() == "c":
                        nome_arquivo2 = "CANCELLED"
                        break
                    elif retry_automaton2.lower() != "s":
                        nome_arquivo2 = "CANCELLED"
                        break
            
            if nome_arquivo2 == "CANCELLED":
                print("Operação de Diferença Simétrica cancelada.")
            elif nome_arquivo2:
                if not os.path.exists(nome_arquivo2):
                    print(f"Erro: O arquivo '{nome_arquivo2}' não foi encontrado. Por favor, selecione um arquivo válido.")
                    continue

                try:
                    arvore_xml2 = ET.parse(nome_arquivo2)
                    raiz_xml2 = arvore_xml2.getroot()
                    automato_xml2 = raiz_xml2.find("automaton")
                    if automato_xml2 is None:
                        print(f"Erro: O arquivo '{nome_arquivo2}' não contém uma tag 'automaton' válida. Por favor, verifique o formato do arquivo JFLAP.")
                        continue
                except ET.ParseError as e:
                    print(f"Erro ao analisar o arquivo XML do Autômato 2: {e}. Certifique-se de que é um arquivo JFLAP válido.")
                    continue

                estados2 = {}
                transicoes2 = []
                for estado_elemento in automato_xml2.findall("state"):
                    id_estado = estado_elemento.get("id")
                    nome_estado = estado_elemento.get("name")
                    estados2[id_estado] = {
                        "nome": nome_estado,
                        "inicial": estado_elemento.find("initial") is not None,
                        "final": estado_elemento.find("final") is not None
                    }
                for transicao_elemento in automato_xml2.findall("transition"):
                    de_estado = transicao_elemento.find("from").text
                    para_estado = transicao_elemento.find("to").text
                    leitura = transicao_elemento.find(
                        "read").text if transicao_elemento.find("read") is not None else "ε"
                    transicoes2.append((de_estado, para_estado, leitura))

                alfabeto2 = set()
                for _, _, simbolo in transicoes2:
                    if simbolo != "ε":
                        alfabeto2.add(simbolo)

                novos_estados, novas_transicoes = aplicar_diferenca_simetrica(
                    estados1, transicoes1, alfabeto1, estados2, transicoes2, alfabeto2)
                if novos_estados is not None:
                    print("\nOperação de Diferença Simétrica aplicada.")
        else:
            break

        print("\nDeseja fazer outra operação? (S ou N)")
        entrada = input()

    print("Fim do programa")

if __name__ == "__main__":
    main()
