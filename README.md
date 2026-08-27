# 🧾 Agente Romaneio — Foto para PDF com IA

Agente de IA que lê a foto de um romaneio de compras manuscrito, extrai os
dados automaticamente (usando visão multimodal do Claude) e gera um PDF
formatado e pronto para uso — sem digitação manual.

## Motivação por tras do projeto

Meu pai costuma fazer romaneios de compras à mão que depois são digitalizados
manualmente em planilhas, um processo lento e que pode ser agilizado para os funcionários com a ajuda da IA.
Este agente automatiza essa etapa: você tira uma foto, confere os dados
extraídos numa interface simples, e exporta um PDF organizado.

## 🏗️ Arquitetura

```
Foto do romaneio
      │
      ▼
Frontend (HTML/JS) ──envia imagem──▶ Backend (FastAPI)
                                           │
                                           ▼
                                  Claude (visão multimodal)
                                           │
                                           ▼
                                  Extração estruturada (JSON)
                                           │
                                           ▼
                                  Geração de PDF (ReportLab)
                                           │
                                           ▼
                                  PDF pronto para download
```

**Stack:** Python · FastAPI · Anthropic Claude API · ReportLab · HTML/CSS/JS puro · Docker

## 📁 Estrutura do projeto

```
agente-romaneio-pdf/
├── backend/
│   ├── main.py           
│   └── requirements.txt
├── frontend/
│   └── index.html        
├── Dockerfile
├── .dockerignore
└── .env.example
```

## 🚀 Como rodar localmente

### Pré-requisitos
- Baixe a imagem exemplo que deixei disponivel, pois a versão atual só funciona
  com um modelo especifico de romaneio (em breve sera atualizado para rodar em qualquer tipo de imagem)
- [Docker](https://www.docker.com/get-started) instalado, **ou** Python 3.11+
- Uma chave de API da Anthropic — gere gratuitamente em
  [console.anthropic.com](https://console.anthropic.com/settings/keys)
  (é necessário adicionar um cartão para gerar créditos, mas o custo de
  teste deste projeto é de poucos centavos)

### Opção A — Com Docker (recomendado)

```bash
git clone https://github.com/konomijk/agente-romaneio-pdf.git
cd agente-romaneio-pdf

# Configure sua chave
cp .env.example .env
# edite o .env e cole sua chave (ANTHROPIC_API_KEY=sk-ant-...)

# Build e execução
docker build -t agente-romaneio .
docker run --env-file .env -p 8080:8080 agente-romaneio
```

Acesse: **http://localhost:8080**

### Opção B — Sem Docker

```bash
git clone https://github.com/konomijk/agente-romaneio-pdf.git
cd agente-romaneio-pdf/backend

pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx   # Windows: set ANTHROPIC_API_KEY=...

uvicorn main:app --reload --port 8080
```

Acesse: **http://localhost:8080**

## 🧪 Como testar

1. Abra o app no navegador
2. Envie a foto de qualquer documento manuscrito com uma tabela simples
   (ou use uma foto de teste — posso indicar exemplos se necessário)
3. Clique em **"Processar romaneio"** e aguarde a extração
4. Confira/edite os dados na tabela exibida
5. Clique em **"Baixar PDF"** para gerar o arquivo final

## 🔐 Sobre a chave de API

Este projeto **não inclui** nenhuma chave de API por motivos óbvios de
segurança. Cada pessoa que rodar o projeto usa a própria chave, criada
gratuitamente no Console da Anthropic. O uso de teste (poucas imagens)
custa frações de centavo.

## 📌 Decisões técnicas

- **Backend separado do frontend**: a chamada à API da Anthropic acontece
  inteiramente no servidor, nunca no navegador — evita expor a chave.
- **PDF gerado no servidor** (ReportLab), não no navegador: mais confiável
  e evita problemas de bloqueio de scripts externos em ambientes restritos.
- **Dados editáveis antes da exportação**: como a extração por IA pode
  errar em caligrafias difíceis, a interface permite revisão manual antes
  de gerar o PDF final.


---

Projeto pessoal desenvolvido para estudo de agentes de IA aplicados a
automação de documentos.
