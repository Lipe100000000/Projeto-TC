from google.colab import files
import xml.etree.ElementTree as ET

#ESTRELA--------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def aplicar_estrela(estados, transicoes, arvore_xml, automato_xml, nome_saida="estrela_aplicada.jff"):
    novos_ids = [int(i) for i in estados.keys() if i.isdigit()]
    novo_id_estado = str(max(novos_ids) + 1 if novos_ids else 0)
    novo_nome_estado = f"q{novo_id_estado}"

    estado_inicial_antigo = None
    for id_estado, info_estado in estados.items():
        if info_estado["inicial"]:
            estado_inicial_antigo = id_estado
            estados[id_estado]["inicial"] = False
            break

    if estado_inicial_antigo is None:
        raise ValueError("Autômato não possui estado inicial definido.")

    estados[novo_id_estado] = {
        "nome": novo_nome_estado,
        "inicial": True,
        "final": True
    }

    transicoes.append((novo_id_estado, estado_inicial_antigo, "ε"))

    for id_estado, info_estado in estados.items():
        if info_estado["final"] and id_estado != novo_id_estado:
            transicoes.append((id_estado, estado_inicial_antigo, "ε"))

    for elemento in automato_xml.findall("state") + automato_xml.findall("transition"):
        automato_xml.remove(elemento)

    for id_estado, info_estado in estados.items():
        elemento_estado_xml = ET.SubElement(automato_xml, "state", id=id_estado, name=info_estado["nome"])
        if info_estado["inicial"]:
            ET.SubElement(elemento_estado_xml, "initial")
        if info_estado["final"]:
            ET.SubElement(elemento_estado_xml, "final")

    for de_estado, para_estado, simbolo in transicoes:
        elemento_transicao_xml = ET.SubElement(automato_xml, "transition")
        ET.SubElement(elemento_transicao_xml, "from").text = de_estado
        ET.SubElement(elemento_transicao_xml, "to").text = para_estado
        ET.SubElement(elemento_transicao_xml, "read").text = "" if simbolo == "ε" else simbolo

    arvore_xml.write(nome_saida, encoding="utf-8", xml_declaration=True)
    print(f"\nArquivo '{nome_saida}' salvo com sucesso.")

    return estados, transicoes

#COMPLETO--------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def eh_completo(estados, transicoes, alfabeto):

    for _, _, simbolo in transicoes:
        if simbolo == "ε":
            print("Erro: O autômato possui transições epsilon. Não é um AFD completo.")
            return False

    transicoes_por_estado_simbolo = {}
    for de_estado, _, simbolo in transicoes:
        if (de_estado, simbolo) in transicoes_por_estado_simbolo:
            print(f"Erro: O autômato possui múltiplas transições para o estado {estados[de_estado]['nome']} com o símbolo '{simbolo}'. Não é um AFD completo.")
            return False
        transicoes_por_estado_simbolo[(de_estado, simbolo)] = True

    for id_estado in estados.keys():
        for simbolo in alfabeto:
            if (id_estado, simbolo) not in transicoes_por_estado_simbolo:
                print(f"Erro: O estado {estados[id_estado]['nome']} não possui transição para o símbolo '{simbolo}'. O autômato não é completo.")
                return False
    return True

#COMPLEMENTO-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def aplicar_complemento(estados, transicoes, arvore_xml, automato_xml, alfabeto, nome_saida="complemento_aplicado.jff"):

    if not eh_completo(estados, transicoes, alfabeto):
        print("Erro: O autômato não é um AFD completo. Não é possível aplicar o complemento.")
        return estados, transicoes

    for id_estado in estados:
        estados[id_estado]["final"] = not estados[id_estado]["final"]

    for elemento in automato_xml.findall("state"):
        automato_xml.remove(elemento)

    for id_estado, info_estado in estados.items():
        elemento_estado_xml = ET.SubElement(automato_xml, "state", id=id_estado, name=info_estado["nome"])
        if info_estado["inicial"]:
            ET.SubElement(elemento_estado_xml, "initial")
        if info_estado["final"]:
            ET.SubElement(elemento_estado_xml, "final")


    arvore_xml.write(nome_saida, encoding="utf-8", xml_declaration=True)
    print(f"\nArquivo '{nome_saida}' salvo com sucesso.")

    return estados, transicoes

# DIFERENÇA SIMÉTRICA ------------------------------------------------------------------------------------------------------------------------------------------------------------
def aplicar_diferenca_simetrica(estados1, transicoes1, alfabeto1, estados2, transicoes2, alfabeto2,nome_saida="diferenca_simetrica_aplicada.jff"):

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

    mapa_ids1 = {id_e: estados1[id_e]["nome"] for id_e in estados1}
    mapa_ids2 = {id_e: estados2[id_e]["nome"] for id_e in estados2}

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
        print("Erro: Não foi possível determinar o estado inicial do autômato resultante.")
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
            print(f"Aviso: Não foi possível mapear o nome combinado {info_novo_s['nome']} de volta aos IDs originais.")

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
                id_destino_novo = tabela_busca_id_estado.get((id_destino1, id_destino2))
                if id_destino_novo is not None:
                    novas_transicoes.append((id_atual_novo, id_destino_novo, simbolo_alfabeto))
                else:
                    print(f"Aviso: Não encontrou o novo estado de destino para ({id_destino1},{id_destino2}) com símbolo {simbolo_alfabeto}.")
            else:
                 print(f"Aviso: Autômato incompleto ou símbolo ausente para ({id_atual1_original},{id_atual2_original}) no símbolo '{simbolo_alfabeto}'.")

    raiz_xml = ET.Element("structure")
    ET.SubElement(raiz_xml, "type").text = "fa"
    elemento_automato_xml = ET.SubElement(raiz_xml, "automaton")

    for id_estado, info_estado in novos_estados.items():
        elemento_estado_xml = ET.SubElement(elemento_automato_xml, "state", id=id_estado, name=info_estado["nome"])
        ET.SubElement(elemento_estado_xml, "x").text = "0"
        ET.SubElement(elemento_estado_xml, "y").text = "0"
        if info_estado["inicial"]:
            ET.SubElement(elemento_estado_xml, "initial")
        if info_estado["final"]:
            ET.SubElement(elemento_estado_xml, "final")

    for de_estado, para_estado, simbolo in novas_transicoes:
        elemento_transicao_xml = ET.SubElement(elemento_automato_xml, "transition")
        ET.SubElement(elemento_transicao_xml, "from").text = de_estado
        ET.SubElement(elemento_transicao_xml, "to").text = para_estado
        ET.SubElement(elemento_transicao_xml, "read").text = "" if simbolo == "ε" else simbolo

    nova_arvore_xml = ET.ElementTree(raiz_xml)
    nova_arvore_xml.write(nome_saida, encoding="utf-8", xml_declaration=True)
    print(f"\nArquivo '{nome_saida}' salvo com sucesso.")

    return novos_estados, novas_transicoes

# MAIN ------------------------------------------------------------------------------------------------------------------------------------------------------------
entrada = "s"
while entrada == "s" or entrada == "S":
    print("\n--- Carregando Autômato 1 ---")
    arquivos_carregados = files.upload()
    if arquivos_carregados:
        nome_arquivo1 = list(arquivos_carregados.keys())[0]
    else:
        print("Nenhum arquivo foi carregado para o Autômato 1. Reiniciando.")
        continue

    arvore_xml1 = ET.parse(nome_arquivo1)
    raiz_xml1 = arvore_xml1.getroot()

    automato_xml1 = raiz_xml1.find("automaton")

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
        leitura = transicao_elemento.find("read").text if transicao_elemento.find("read") is not None else "ε"

        transicoes1.append((de_estado, para_estado, leitura))

    alfabeto1 = set()
    for _, _, simbolo in transicoes1:
        if simbolo != "ε":
            alfabeto1.add(simbolo)

    print("\nDigite 1 para realizar a operação ESTRELA (no Autômato 1)")
    print("Digite 2 para realizar a operação COMPLEMENTO (no Autômato 1)")
    print("Digite 3 para realizar a operação DIFERENÇA SIMÉTRICA (requer 2 autômatos)")
    print("Digite qualquer outra tecla para sair")
    entrada_usuario = input()

    if entrada_usuario == "1":
        estados1, transicoes1 = aplicar_estrela(estados1, transicoes1, arvore_xml1, automato_xml1)
    elif entrada_usuario == "2":
        estados1, transicoes1 = aplicar_complemento(estados1, transicoes1, arvore_xml1, automato_xml1, alfabeto1)
    elif entrada_usuario == "3":
        print("\n--- Carregando Autômato 2 para Diferença Simétrica ---")
        arquivos_carregados2 = files.upload()
        if arquivos_carregados2:
            nome_arquivo2 = list(arquivos_carregados2.keys())[0]
        else:
            print("Nenhum arquivo foi carregado para o Autômato 2. Operação cancelada.")
            continue

        arvore_xml2 = ET.parse(nome_arquivo2)
        raiz_xml2 = arvore_xml2.getroot()
        automato_xml2 = raiz_xml2.find("automaton")

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
            leitura = transicao_elemento.find("read").text if transicao_elemento.find("read") is not None else "ε"
            transicoes2.append((de_estado, para_estado, leitura))

        alfabeto2 = set()
        for _, _, simbolo in transicoes2:
            if simbolo != "ε":
                alfabeto2.add(simbolo)

        novos_estados, novas_transicoes = aplicar_diferenca_simetrica(estados1, transicoes1, alfabeto1, estados2, transicoes2, alfabeto2)
        if novos_estados is not None:
            print("\nOperação de Diferença Simétrica aplicada.")

    else:
        break

    print("\nDeseja fazer outra operação? (S ou N)")
    entrada = input()
print("Fim do programa")
