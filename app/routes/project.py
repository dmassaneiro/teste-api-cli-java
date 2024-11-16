from time import sleep

from flask import Blueprint, jsonify, request

bp = Blueprint('project', __name__, url_prefix='/projects')

import zipfile
import os
import tempfile
import shutil
import io
import uuid
import xml.etree.ElementTree as ET
from xml.dom import minidom


# Endpoint para listar todos os projetos
@bp.route('/new', methods=['POST'])
def post_projects():
    name = request.json.get('name')
    description = request.json.get('description')
    group = request.json.get('group')
    dependencies = request.json.get('dependencies')

    # baixar base do projeto
    arquivo(name, description, dependencies)

    return "Feito."


def arquivo(name, description, dependencies):
    print("baixando arquivo...")
    zip_path = './download/demo.zip'

    shutil.rmtree("./download/teste")

    print("criando pasta temporaria...")
    # uid = uuid.uuid4()
    uid = "teste"
    destino = f"./download/{uid}"

    print("extraindo dados para a pasta temporaria...")
    extrair_zip(zip_path, destino)

    sleep(3)
    print("renomeando pastas...")
    renomear_pastas(destino, "nova_demo", name)

    # sleep(3)
    print("renomeando alterando pom...")
    alterar_pom(f"{destino}/{name}", dependencies, name, description)

    # sleep(3)
    print("renomeando alterando properties...")
    alterar_properties(f"{destino}/{name}/src/main/resources", dependencies)

    # print("zipando para enviar para download...")

    # altera_pom(zip_path)
    # sleep(10)

    # print("deletando arquivos...")
    # deleta pasta
    # shutil.rmtree(destino)


def extrair_zip(zip_path, pasta_destino):
    # Verificar se o arquivo zip existe
    if not os.path.exists(zip_path):
        print(f"O arquivo {zip_path} não foi encontrado.")
        return

    # Criar a pasta de destino, caso não exista
    os.makedirs(pasta_destino, exist_ok=True)

    try:
        # Abrir o arquivo zip
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Extrair todo o conteúdo para a pasta de destino
            zip_ref.extractall(pasta_destino)


    except zipfile.BadZipFile:
        print(f"O arquivo {zip_path} não é um arquivo ZIP válido.")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")


def renomear_pasta(pasta_antiga, pasta_nova):
    if os.path.exists(pasta_antiga) and os.path.isdir(pasta_antiga):
        os.rename(pasta_antiga, pasta_nova)
    else:
        print(f"A pasta '{pasta_antiga}' não existe.")


def renomear_pastas(diretorio_raiz, nome_antigo, nome_novo):
    # Caminha recursivamente pelos diretórios e subdiretórios
    for root, dirs, files in os.walk(diretorio_raiz, topdown=False):
        for dir_name in dirs:
            # Verifica se o diretório contém o nome antigo
            if nome_antigo in dir_name:
                # Caminho completo do diretório a ser renomeado
                caminho_antigo = os.path.join(root, dir_name)
                caminho_novo = os.path.join(root, dir_name.replace(nome_antigo, nome_novo))

                # Renomeia o diretório
                os.rename(caminho_antigo, caminho_novo)

    deleta_pasta(f"{diretorio_raiz}/{nome_novo}/target")

def alterar_pom(diretorio_raiz, depend, name, description):
    novo_arquivo = f'{diretorio_raiz}/novo_pom.xml'
    # Carregar o XML
    tree = ET.parse(f"{diretorio_raiz}/pom.xml")
    root = tree.getroot()

    # Definir o namespace para acessar corretamente as tags
    namespace = {'maven': 'http://maven.apache.org/POM/4.0.0'}

    # Alterar o valor das tags <name> e <description>
    name_tag = root.find('.//maven:name', namespace)
    description_tag = root.find('.//maven:description', namespace)

    if name_tag is not None:
        name_tag.text = name
    if description_tag is not None:
        description_tag.text = description

    # Lista de dependências padrão (já existentes no POM)
    lib_default = [
        'spring-boot-starter-web',
        'spring-boot-starter-logging',
        'lombok',
        'micrometer-tracing-bridge-brave',
        'spring-boot-starter-actuator',
        'spring-boot-starter-test'
    ]

    # Combinando dependências padrão com as adicionais passadas
    lib_combinada = lib_default + depend

    # Iterando sobre todas as dependências no XML
    dependencies = root.findall('.//maven:dependencies/maven:dependency', namespace)
    for item in dependencies:
        artifact_id = item.find('maven:artifactId', namespace).text if item.find('maven:artifactId',
                                                                                 namespace) is not None else 'N/A'

        # Verificar se o artifact_id está na lista combinada
        if artifact_id in lib_combinada:
            print(f'Exibe (mantém): {artifact_id}')
        else:
            print(f'Remove (não existe na lista): {artifact_id}')
            # Encontrar a tag <dependencies> e remover a dependência
            parent = root.find('.//maven:dependencies', namespace)
            parent.remove(item)

    # Remover o namespace das tags
    for elem in root.iter():
        # Remover o prefixo 'ns0:' ou qualquer prefixo na tag
        elem.tag = elem.tag.split('}')[1] if '}' in elem.tag else elem.tag

    # Função para salvar o XML com indentação original e a declaração XML correta
    def save_xml(tree, output_file):
        # Converter a árvore XML para uma string sem formatação (usando ElementTree.write)
        with open(output_file, "wb") as f:
            tree.write(f, encoding='utf-8', xml_declaration=True)

    # Salvando o XML modificado no novo arquivo
    save_xml(tree, novo_arquivo)

    # remove pom antigo
    os.remove(f"{diretorio_raiz}/pom.xml")
    # altera nome pom novo
    os.rename(f"{diretorio_raiz}/novo_pom.xml", f"{diretorio_raiz}/pom.xml")

def alterar_properties(diretorio_raiz, deps):
    caminho_arquivo = f"{diretorio_raiz}/application-dev.properties"

    prefixos_para_remover = []
    if "spring-boot-starter-data-jpa" not in deps:
        # Lista dos prefixos das propriedades a serem removidas
        prefixos_para_remover = [
            'spring.jpa.show-sql',
            'spring.jpa.hibernate.ddl-auto',
            'spring.datasource.url',
            'spring.datasource.username',
            'spring.datasource.password',
            'spring.datasource.driver-class-name',
        ]

    # Ler o arquivo de propriedades
    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
        linhas = f.readlines()

    # Filtrar as linhas, removendo as que começam com os prefixos fornecidos
    linhas_filtradas = [
        linha for linha in linhas if not any(linha.strip().startswith(prefix) for prefix in prefixos_para_remover)
    ]

    # Sobrescrever o arquivo com as linhas filtradas
    with open(caminho_arquivo, 'w', encoding='utf-8') as f:
        f.writelines(linhas_filtradas)


def deleta_pasta(folder_path):
    if os.path.exists(folder_path):
        try:
            shutil.rmtree(folder_path)
            print(f"A pasta {folder_path} e todo o seu conteúdo foram removidos com sucesso.")
        except Exception as e:
            print(f"Erro ao remover a pasta {folder_path}: {e}")
    else:
        print(f"A pasta {folder_path} não foi encontrada.")