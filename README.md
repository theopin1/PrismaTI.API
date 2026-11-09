# PrismaTI API

Backend de avaliação de maturidade de TI desenvolvido em Python com Flask e PostgreSQL.

A API oferece autenticação, gestão de empresas e usuários, questionários versionados, avaliações, respostas, cálculo de maturidade, evidências, auditoria e relatórios com exportação em PDF.

## Tecnologias

- Python 3.11 ou superior
- Flask
- PostgreSQL
- SQLAlchemy
- Alembic
- Pytest
- ReportLab

## Como executar

### 1. Clonar o repositório

```bash
git clone https://github.com/theopin1/PrismaTI.API.git
cd PrismaTI.API
```

### 2. Criar o ambiente virtual e instalar as dependências

No Windows, usando PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
$env:PYTHONPATH = 'src'
```

No Linux ou macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=src
```

Ao abrir um novo terminal, configure novamente o `PYTHONPATH`.

### 3. Configurar o PostgreSQL e o arquivo .env

O PostgreSQL precisa estar em execução, com banco e usuário previamente criados.

Copie o arquivo `.env.example` para `.env`:

```powershell
Copy-Item .env.example .env
```

No Linux ou macOS:

```bash
cp .env.example .env
```

Configure os valores:

```dotenv
DATABASE_URL=postgresql+psycopg://prismati:SUA_SENHA@localhost:5432/prismati
SECRET_KEY=SUBSTITUA_POR_UM_SEGREDO_ALEATORIO
FLASK_DEBUG=0
```

A `SECRET_KEY` precisa ter pelo menos 32 caracteres. Para gerar um valor:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

O arquivo `.env` contém credenciais e deve permanecer fora do controle de versão.

### 4. Aplicar as migrações

No Windows:

```powershell
.venv\Scripts\python -m alembic upgrade head
```

No Linux ou macOS, com o ambiente virtual ativado:

```bash
python -m alembic upgrade head
```

### 5. Criar o primeiro administrador

No Windows:

```powershell
.venv\Scripts\python -m flask --app prismati.bootstrap.app_factory:create_app create-admin
```

No Linux ou macOS:

```bash
python -m flask --app prismati.bootstrap.app_factory:create_app create-admin
```

O comando solicita nome, e-mail e senha. A senha deve ter no mínimo 7 caracteres.

### 6. Iniciar a API

No Windows:

```powershell
.venv\Scripts\python -m flask --app prismati.bootstrap.app_factory:create_app run --host 127.0.0.1 --port 5000
```

No Linux ou macOS:

```bash
python -m flask --app prismati.bootstrap.app_factory:create_app run --host 127.0.0.1 --port 5000
```

Endereços locais:

| Serviço | Endereço |
|---|---|
| Base da API | http://127.0.0.1:5000/api |
| Swagger | http://127.0.0.1:5000/documentacao |
| Especificação OpenAPI | http://127.0.0.1:5000/openapi.json |
| Verificação de disponibilidade | http://127.0.0.1:5000/api/saude |

O Swagger utiliza recursos de um CDN e precisa de acesso à internet.

O comando `flask run` inicia o servidor de desenvolvimento.

## Autenticação

Faça login em:

```http
POST /api/autenticacao/entrar
Content-Type: application/json
```

```json
{
  "email": "admin@example.com",
  "senha": "sua-senha"
}
```

Resposta:

```json
{
  "access_token": "TOKEN_RETORNADO",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

Envie o token nas requisições protegidas:

```http
Authorization: Bearer TOKEN_RETORNADO
```

O token expira em uma hora. Ao receber HTTP 401, o frontend deve solicitar uma nova autenticação.

O token deve ser tratado como um valor opaco. O login retorna somente o token, seu tipo e sua validade. Atualmente não existem endpoints específicos de `/me`, logout ou renovação de token.

No Swagger, clique em **Authorize** e cole somente o valor de `access_token`.

O login permite 20 tentativas por endereço IP em uma janela de cinco minutos, incluindo tentativas bem-sucedidas.

## Perfis e permissões

| Perfil | Uso |
|---|---|
| `ADMIN` | Gerencia empresas, usuários, vínculos e instrumentos. Consulta avaliações, resultados e auditoria. Pode solicitar relatórios. |
| `MANAGER` | Gestor da empresa. Cria avaliações e altera respostas, evidências e finaliza as avaliações pelas quais é responsável. |
| `IT_RESPONSIBLE` | Consulta os dados permitidos da empresa à qual está vinculado. |

Usuários empresariais precisam de um vínculo com uma empresa ativa. Cada usuário pode ter apenas um vínculo.

A escrita nas avaliações e respostas exige que o usuário seja o gestor responsável, inclusive quando há um administrador autenticado.

### Status de usuário

| Valor | Comportamento |
|---|---|
| `PENDING` | Aguardando ativação. Login bloqueado. É o padrão ao omitir o campo no cadastro. |
| `ACTIVE` | Conta ativa e habilitada para login. |
| `INACTIVE` | Conta desativada e com acesso bloqueado. |

## Endpoints disponíveis

Todos os caminhos abaixo utilizam o prefixo `/api`.

### Autenticação e convites

| Método | Caminho | Autenticação | Finalidade |
|---|---|---|---|
| GET | `/saude` | Pública | Verificar disponibilidade da API |
| POST | `/autenticacao/entrar` | Pública | Obter token |
| POST | `/autenticacao/recuperar-senha` | Pública | Solicitar código de recuperação |
| POST | `/autenticacao/redefinir-senha` | Pública | Alterar senha com o código recebido |
| POST | `/convites` | Administrador | Enviar convite para uma empresa |
| POST | `/convites/aceitar` | Pública | Criar e ativar a conta pelo convite |

Corpos das requisições:

```json
{
  "email": "gestor@example.com",
  "empresa_id": "UUID_DA_EMPRESA",
  "role": "MANAGER"
}
```

O exemplo acima é usado em `POST /convites`. O perfil pode ser `MANAGER` ou `IT_RESPONSIBLE`. Quando omitido, será `MANAGER`.

Para aceitar o convite:

```json
{
  "token": "CODIGO_RECEBIDO_POR_EMAIL",
  "nome": "Nome do usuário",
  "senha": "sua-senha"
}
```

Para solicitar recuperação:

```json
{
  "email": "gestor@example.com"
}
```

Para redefinir a senha:

```json
{
  "token": "CODIGO_RECEBIDO_POR_EMAIL",
  "senha": "nova-senha"
}
```

O código do convite vale 72 horas. O código de recuperação vale uma hora. Ambos são de uso único.

O aceite do convite já cria o usuário ativo e seu vínculo com a empresa. Depois, o usuário pode fazer login.

### Cadastros e avaliações

Os recursos abaixo possuem as seguintes operações:

| Método | Caminho | Comportamento |
|---|---|---|
| GET | `/{recurso}` | Listar registros permitidos |
| GET | `/{recurso}/{id}` | Consultar um registro |
| POST | `/{recurso}` | Criar um registro |
| PATCH | `/{recurso}/{id}` | Atualizar campos |
| DELETE | `/{recurso}/{id}` | Excluir ou inativar, conforme as regras do recurso |

| Recurso | Campos usados no cadastro |
|---|---|
| `empresas` | `razao_social`, `cnpj`, `segmento`, `porte`, `status` opcional |
| `usuarios` | `nome`, `email`, `senha`, `role`, `status` opcional |
| `vinculos` | `empresa_id`, `usuario_id` |
| `questionarios` | `nome`, `descricao` |
| `versoes` | `questionario_id`, `versao`, `versao_metodologia` |
| `dimensoes` | `versao_questionario_id`, `nome`, `descricao`, `ordem`, `codigo` |
| `perguntas` | `dimensao_id`, `texto`, `ordem`, `codigo`, `explicacao`, `orientacao_evidencia` |
| `alternativas` | `pergunta_id`, `descricao`, `pontuacao`, `ordem` |
| `avaliacoes` | `empresa_id`, `versao_questionario_id` |
| `respostas` | `avaliacao_id`, `pergunta_id`, `tipo_resposta`, `alternativa_id`, `justificativa` |

Consulte o Swagger para identificar os campos obrigatórios e seus tipos. IDs, datas e outros campos calculados são definidos pelo backend.

Regras de exclusão:

- Empresas e usuários são inativados.
- Avaliações não podem ser excluídas.
- Registros referenciados por outros registros possuem exclusão restrita.
- Instrumentos publicados e avaliações finalizadas possuem bloqueios de alteração.

### Operações específicas

| Método | Caminho | Finalidade |
|---|---|---|
| POST | `/versoes/{id}/publicar` | Publicar uma versão válida |
| POST | `/avaliacoes/{id}/finalizar` | Calcular, salvar o resultado e finalizar |
| GET | `/avaliacoes/{id}/resultado` | Consultar o resultado salvo |
| GET | `/respostas/{id}/evidencias` | Listar evidências de uma resposta |
| POST | `/respostas/{id}/evidencias` | Anexar arquivo ou link |
| GET | `/evidencias/{id}` | Baixar arquivo ou obter o link |
| DELETE | `/evidencias/{id}` | Excluir evidência |
| POST | `/avaliacoes/{id}/relatorios` | Solicitar uma nova geração de relatório |
| GET | `/avaliacoes/{id}/relatorios` | Consultar as gerações e seus resultados |
| GET | `/relatorios/{id}/pdf` | Baixar PDF de um relatório concluído |
| GET | `/auditoria` | Consultar as últimas 100 alterações como administrador |

Publicação, finalização e solicitação de relatório não exigem corpo JSON.

## Listagens e paginação

As listagens dos recursos de cadastro usam:

```http
GET /api/perguntas?offset=0&limit=50
```

- `offset` deve ser maior ou igual a zero.
- `limit` aceita valores de 1 a 100.
- Os padrões são `offset=0` e `limit=50`.

Formato da resposta:

```json
{
  "items": [],
  "total": 0
}
```

O `total` representa os registros acessíveis ao usuário antes da paginação.

As listagens de evidências, relatórios e auditoria retornam arrays diretamente.

### Montagem do questionário no frontend

A API atual não fornece uma árvore completa do questionário em uma única chamada nem filtros por relacionamento nas listagens.

Para montar a tela:

1. Obtenha as dimensões e selecione as que pertencem à `versao_questionario_id`.
2. Obtenha as perguntas e agrupe-as pelo `dimensao_id`.
3. Obtenha as alternativas e agrupe-as pelo `pergunta_id`.
4. Ordene dimensões, perguntas e alternativas pelo campo `ordem`.
5. Relacione as respostas existentes pelo `pergunta_id` e pela avaliação.

Carregue todas as páginas necessárias antes de filtrar os dados no frontend. As listagens atuais retornam os registros por ID.

## Fluxo de uma avaliação

1. O administrador cadastra a empresa.
2. Cadastra e vincula um gestor ativo ou envia um convite.
3. Cadastra o questionário, a versão, as dimensões, as perguntas e as alternativas.
4. Publica a versão.
5. O gestor faz login e cria uma avaliação com a empresa e a versão publicada.
6. Salva as respostas e, quando necessário, anexa evidências.
7. Finaliza a avaliação.
8. Consulta o resultado e solicita um relatório.

Existe uma restrição de uma avaliação em andamento por empresa.

### Questionários versionados

O questionário identifica o instrumento. Cada versão guarda uma edição das dimensões, perguntas e alternativas.

A avaliação aponta para uma versão específica, preservando o histórico do que foi respondido.

A publicação atual exige:

- Sete dimensões.
- Trinta perguntas, distribuídas em grupos de 3, 4, 4, 4, 5, 5 e 5.
- Cinco alternativas por pergunta, com pontuações de 0 a 4.

Uma versão publicada fica bloqueada para edição.

## Respostas

Uma avaliação permite uma resposta por pergunta. Para alterar uma resposta existente, use `PATCH /api/respostas/{id}` com o ID da resposta.

### Resposta com pontuação

```json
{
  "avaliacao_id": "UUID_DA_AVALIACAO",
  "pergunta_id": "UUID_DA_PERGUNTA",
  "tipo_resposta": "SCORED",
  "alternativa_id": "UUID_DA_ALTERNATIVA"
}
```

A nota é obtida da alternativa escolhida.

### Não se aplica

```json
{
  "avaliacao_id": "UUID_DA_AVALIACAO",
  "pergunta_id": "UUID_DA_PERGUNTA",
  "tipo_resposta": "NA",
  "alternativa_id": null,
  "justificativa": "Justificativa para a pergunta não se aplicar."
}
```

### Não sabe

```json
{
  "avaliacao_id": "UUID_DA_AVALIACAO",
  "pergunta_id": "UUID_DA_PERGUNTA",
  "tipo_resposta": "NS",
  "alternativa_id": null
}
```

Ao trocar uma resposta de `SCORED` para `NA` ou `NS`, envie explicitamente `"alternativa_id": null` no PATCH para limpar a alternativa anterior.

A API define automaticamente a versão do questionário, o autor e a data da última atualização.

## Resultado e finalização

O gestor responsável finaliza com:

```http
POST /api/avaliacoes/{id}/finalizar
```

O backend calcula e salva o resultado e fecha a avaliação na mesma transação. Repetir essa chamada retorna o resultado já salvo.

A finalização bloqueia alterações na avaliação, nas respostas e nas evidências.

Avaliações incompletas também podem ser finalizadas. O frontend deve confirmar essa ação com o usuário, pois o fluxo atual não oferece reabertura.

O resultado inclui:

- `maturidade_geral`
- `cobertura`
- `preenchimento`
- `suficiencia`
- `dimensoes`, com os resultados individuais

### Regras de cálculo

```text
Maturidade da dimensão =
soma das notas / (quantidade de respostas numéricas × 4) × 100

Maturidade geral =
média das dimensões com resultado

Cobertura =
respostas numéricas / (total de perguntas − respostas NA) × 100

Preenchimento =
perguntas respondidas / total de perguntas × 100
```

Todas as dimensões têm o mesmo peso na maturidade geral.

| Resposta | Efeito |
|---|---|
| Nota zero | É uma resposta numérica válida e reduz a maturidade |
| `NA` | Exige justificativa e é excluída da base da cobertura |
| `NS` | Conta como preenchida, mas reduz a cobertura |
| Não respondida | Reduz preenchimento e cobertura |

Maturidade sem dados numéricos é retornada como `null`. O frontend deve exibir “Sem dados” ou equivalente.

| Suficiência | Significado |
|---|---|
| `READY_FOR_REVIEW` | Cobertura de pelo menos 80% e resultado em todas as dimensões |
| `PRELIMINARY` | Existem notas, mas os critérios acima não foram atendidos |
| `INSUFFICIENT_DATA` | Nenhuma resposta numérica |

## Evidências

As evidências pertencem a uma resposta. Uma resposta pode ter vários arquivos ou links.

Para anexar um arquivo, envie `multipart/form-data` com o campo `arquivo`. O limite por arquivo é 10 MiB.

No navegador:

```javascript
const form = new FormData();
form.append("arquivo", arquivoSelecionado);

const response = await fetch(
  \`http://127.0.0.1:5000/api/respostas/\${respostaId}/evidencias\`,
  {
    method: "POST",
    headers: {
      Authorization: \`Bearer \${token}\`
    },
    body: form
  }
);
```

Ao usar `FormData`, deixe o navegador definir o `Content-Type` e o boundary.

Para anexar um link, envie JSON:

```json
{
  "url": "https://example.com/documento"
}
```

O GET de uma evidência retorna o arquivo para download ou um JSON com `url`, conforme o tipo.

As evidências são opcionais e não alteram a nota de maturidade. Os arquivos são armazenados no PostgreSQL.

## Relatórios e processamento de IA

A geração depende de um provedor de IA configurado e de um worker executado em processo separado.

Exemplo de configuração no `.env`:

```dotenv
AI_API_KEY=SUA_CHAVE
AI_MODEL=MODELO_CONFIGURADO_NO_PROVEDOR
AI_REPORT_LIMIT=10
```

Opcionalmente, configure `AI_ENDPOINT` para um endpoint compatível com Chat Completions. O endereço padrão é `https://api.openai.com/v1/chat/completions`.

O worker envia o resultado consolidado da avaliação ao provedor para interpretação.

No Windows:

```powershell
$env:PYTHONPATH = 'src'
.venv\Scripts\python -m flask --app prismati.bootstrap.app_factory:create_app processar-relatorios --continuo
```

No Linux ou macOS:

```bash
export PYTHONPATH=src
python -m flask --app prismati.bootstrap.app_factory:create_app processar-relatorios --continuo
```

### Uso pelo frontend

1. Envie `POST /api/avaliacoes/{id}/relatorios`.
2. Guarde o ID retornado. A resposta HTTP 202 indica que a solicitação foi registrada.
3. Consulte periodicamente `GET /api/avaliacoes/{id}/relatorios`.
4. Quando o registro estiver `COMPLETED`, exiba `texto` e habilite o download do PDF.
5. Se estiver `FAILED`, informe a falha ao usuário.

Os estados atualmente gravados são `PENDING`, `COMPLETED` e `FAILED`. Durante o processamento, o registro permanece visível como `PENDING`.

Cada POST cria uma nova solicitação. O limite padrão é de dez solicitações por avaliação, incluindo falhas. Sem worker em execução, as solicitações permanecem pendentes.

## Configuração de e-mail

Convites e recuperação de senha dependem de SMTP:

```dotenv
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_FROM=prismati@example.com
SMTP_STARTTLS=1
SMTP_USER=SEU_USUARIO
SMTP_PASSWORD=SUA_SENHA
```

O e-mail contém o código que deve ser informado nas telas de aceite ou redefinição de senha.

## Integração do frontend

### Requisições JSON

Use:

```http
Content-Type: application/json
Authorization: Bearer TOKEN_RETORNADO
```

O `Authorization` é dispensado nas rotas públicas.

Campos desconhecidos nos cadastros são rejeitados. Evite enviar o objeto completo recebido da API em um PATCH. Envie somente os campos editáveis.

### Respostas HTTP

| Código | Tratamento esperado |
|---|---|
| 200 | Consulta ou operação concluída |
| 201 | Registro criado |
| 202 | Solicitação aceita |
| 204 | Operação concluída sem corpo |
| 400 | Dados inválidos |
| 401 | Token ausente, inválido, expirado ou usuário inativo |
| 403 | Usuário sem permissão |
| 404 | Registro ou resultado não encontrado |
| 409 | Duplicidade, vínculo protegido ou estado incompatível |
| 413 | Arquivo acima do limite |
| 415 | Tipo de conteúdo inadequado para uma rota JSON |
| 429 | Limite de tentativas ou gerações atingido |
| 503 | Banco indisponível ou serviço necessário sem configuração |

Formato dos erros tratados pela API:

```json
{
  "error": "ValidationError",
  "message": "Descrição do problema."
}
```

Algumas operações também retornam corpo vazio com HTTP 201 ou 202. O frontend deve verificar o corpo antes de chamar `response.json()`. Downloads devem ser tratados como `Blob`.

### CORS

O backend atual não configura CORS.

Se o frontend estiver em outra origem, configure um proxy no servidor de desenvolvimento para encaminhar `/api` à API ou implemente a configuração de CORS no backend.

### Validações importantes

- Senhas exigem pelo menos 7 caracteres.
- E-mails de usuários são normalizados para minúsculas.
- CNPJ aceita o formato numérico ou alfanumérico.
- A normalização do CNPJ remove `.`, `/`, `\` e `-` e converte letras para maiúsculas.
- Após a normalização, o CNPJ deve ter 14 caracteres, com os dois últimos numéricos.
- A validação atual do CNPJ verifica formato e duplicidade.
- A pontuação de uma alternativa deve ser um inteiro de 0 a 4.
- IDs são strings UUID.
- Valores de enum, como `ACTIVE`, `MANAGER` e `SCORED`, devem ser enviados exatamente como documentados.

## Testes

No Windows:

```powershell
$env:PYTHONPATH = 'src'
.venv\Scripts\python -m pytest
```

No Linux ou macOS:

```bash
export PYTHONPATH=src
python -m pytest
```

Para executar também o teste de concorrência no PostgreSQL local:

```powershell
$env:PRISMATI_TEST_POSTGRES = '1'
.venv\Scripts\python -m pytest tests/http/test_finalization.py::test_postgres_finalization_race
```

Esse teste cria e remove esquemas temporários isolados. O usuário do banco precisa ter permissão para criá-los.

## Documentação complementar

- [Execução e endpoints](docs/api.md)
- [Arquitetura do projeto](docs/arquitetura.md)
- Swagger disponível em `/documentacao`
- OpenAPI disponível em `/openapi.json`
