import json
import os
from googleapiclient.discovery import build
from autenticacao_google import get_google_credentials

def deploy_wiki_script():
    creds = get_google_credentials()
    service = build('script', 'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)
    
    # 1. ID do Script Fornecido pelo Usuário
    script_id = '1s5bI-FSTZhQi6kzLi84HGqOsX23tqZu95CD24eQHH8Vk2c9r5Y4lJ0Rk'
    print(f"DEBUG: Realizando deploy no Script ID: {script_id}")

    # 2. Ler arquivos locais
    path_gs = "../wiki_interna/wiki_comentarios.gs"
    path_html = "../wiki_interna/index.html"
    
    with open(path_gs, 'r', encoding='utf-8') as f:
        code_gs = f.read()
    with open(path_html, 'r', encoding='utf-8') as f:
        code_html = f.read()

    # 3. Preparar pacotes para o Apps Script API
    # Nota: Precisamos incluir o appsscript.json (manifesto)
    try:
        project = service.projects().getContent(scriptId=script_id).execute()
        files_json = project.get('files', [])
        
        # Atualizar arquivos existentes ou criar novos
        new_files = []
        # Manter o manifesto original
        manifest = next((f for f in files_json if f['name'] == 'appsscript'), {'name': 'appsscript', 'type': 'JSON', 'source': '{\n  "timeZone": "America/Sao_Paulo",\n  "dependencies": {\n  },\n  "exceptionLogging": "STACKDRIVER",\n  "runtimeVersion": "V8"\n}'})
        new_files.append(manifest)
        
        # Adicionar os nossos
        new_files.append({'name': 'Código', 'type': 'SERVER_JS', 'source': code_gs})
        new_files.append({'name': 'index', 'type': 'HTML', 'source': code_html})

        # 4. Upload do Código
        service.projects().updateContent(scriptId=script_id, body={'files': new_files}).execute()
        print("✅ Código enviado com sucesso!")

        # 5. Criar Nova Versão
        version = service.projects().versions().create(scriptId=script_id, body={'description': 'v4.1 - Automática Via Antigravity'}).execute()
        version_number = version.get('versionNumber')
        print(f"✅ Versão {version_number} criada!")

        # 6. Atualizar Implantação (Deployment)
        deps = service.projects().deployments().list(scriptId=script_id).execute()
        deployments = deps.get('deployments', [])
        if deployments:
            dep_id = deployments[0]['deploymentId']
            service.projects().deployments().update(
                scriptId=script_id, 
                deploymentId=dep_id, 
                body={'deploymentConfig': {'versionNumber': version_number, 'manifestFileName': 'appsscript', 'description': 'v4.1 Post-Auth'}}
            ).execute()
            print(f"🚀 Implantação {dep_id} atualizada para a Versão {version_number}!")
        
        print("\n🎉 MISSÃO CUMPRIDA! Sua Wikipedia está atualizada e pronta no Google Sites.")

    except Exception as e:
        print(f"❌ ERRO NO DEPLOY: {e}")

if __name__ == "__main__":
    deploy_wiki_script()
