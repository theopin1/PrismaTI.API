# Execução e endpoints

Swagger UI disponível em `http://127.0.0.1:5000/documentacao` após iniciar a API. A especificação está em `/openapi.json`. A interface carrega recursos do CDN jsDelivr e precisa de internet. Use POST `/autenticacao/entrar` e cole somente o valor de `access_token` em Authorize. O token não é preservado após recarregar a página.

## Configuração no PowerShell

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
$env:PYTHONPATH = 'src'
# Configure DATABASE_URL no .env antes de executar a migração.
.venv\Scripts\python -m alembic upgrade head
.venv\Scripts\python -m flask --app prismati.bootstrap.app_factory:create_app create-admin
.venv\Scripts\python -m flask --app prismati.bootstrap.app_factory:create_app run
```

É necessário um PostgreSQL em execução e banco/usuário previamente criados. A aplicação não cria o servidor ou contas PostgreSQL. Substitua `CHANGE_ME` na DATABASE_URL do `.env`. Uma SECRET_KEY aleatória foi gerada localmente. `.env.example` é o modelo sem segredos e `.gitignore` protege `.env`.

## Endpoints disponíveis

Prefixo `/api`. Rotas em português, sem acentos. Os nomes internos dos recursos e os campos JSON permanecem iguais. As antigas rotas de negócio em inglês foram substituídas.

- GET `/saude`.
- POST `/autenticacao/entrar`: `email` e `senha`; retorna token Bearer com duração de uma hora.
- GET/POST `/{recurso}`; GET/PATCH/DELETE `/{recurso}/{id}`.
- Recursos: `empresas`, `usuarios`, `vinculos`, `questionarios`, `versoes`, `dimensoes`, `perguntas`, `alternativas`, `avaliacoes`, `respostas`.
- POST `/versoes/{id}/publicar` publica um instrumento válido.

Use `Authorization: Bearer <access_token>`. Listagens aceitam `offset` >= 0 e `limit` entre 1 e 100. A filtragem/paginação atual ocorre na aplicação; otimização no banco fica para evolução.

Somente administradores modificam cadastros e instrumentos. Somente o gestor responsável altera sua avaliação e respostas. O perfil `IT_RESPONSIBLE` é consultivo. DELETE de empresas/usuários inativa; avaliações não podem ser excluídas. Registros referenciados têm exclusão restrita. Publicação bloqueia edição do instrumento.

## Sequência de uso

1. Crie o administrador pelo comando CLI e faça login.
2. Cadastre empresa: `razao_social`, `cnpj`, `segmento`, `porte`.
   O `cnpj` aceita o formato numérico e o alfanumérico. Pontos, barras (`/` e `\`) e hífens são removidos; letras são convertidas em maiúsculas. Após a normalização, exige 14 caracteres: os primeiros 12 aceitam letras de A a Z ou números, e os últimos dois devem ser números. Exemplo: `12.abc.345/01de-35` é salvo como `12ABC34501DE35`. Tamanho incorreto ou caracteres inválidos retornam HTTP 400; CNPJ já cadastrado retorna HTTP 409, independentemente da máscara ou maiúsculas/minúsculas. Esta validação verifica o formato, sem cálculo dos dígitos verificadores ou consulta cadastral.
3. Cadastre usuário: `nome`, `email`, `senha` (mínimo 7 caracteres), `role` (`MANAGER` ou `IT_RESPONSIBLE`) e `status: ACTIVE`.
4. Cadastre vínculo em `vinculos`: `empresa_id`, `usuario_id`. Só pode haver um vínculo por usuário.
5. Cadastre questionário (`nome`, `descricao`) e versão (`questionario_id`, `versao`, `versao_metodologia`).
6. Cadastre dimensões (`versao_questionario_id`, `nome`, `descricao`, `ordem`, `codigo`), perguntas (`dimensao_id`, `texto`, `ordem`, `codigo`, `explicacao`, `orientacao_evidencia`) e alternativas (`pergunta_id`, `descricao`, `pontuacao`, `ordem`).
7. Publique a versão: são exigidas sete dimensões com 3,4,4,4,5,5,5 perguntas, cada pergunta com alternativas 0–4.
8. Autentique o gestor e crie avaliação com `empresa_id`, `versao_questionario_id`.
9. Crie resposta: `avaliacao_id`, `pergunta_id`, `tipo_resposta` (`SCORED`, `NA`, `NS`), `alternativa_id` quando numérica e `justificativa` quando NA. Versão e autor são definidos pelo backend.

## Escopo e validação

```powershell
$env:PYTHONPATH = 'src'
.venv\Scripts\python -m pytest
.venv\Scripts\python -m alembic upgrade head --sql
```

O gestor responsável finaliza com POST /api/avaliacoes/{id}/finalizar. A API salva o cálculo e fecha a avaliação na mesma transação. Repetir a chamada retorna o mesmo resultado. GET /api/avaliacoes/{id}/resultado consulta o resultado conforme as permissões da avaliação. Avaliações incompletas podem ser fechadas com a classificação de suficiência correspondente.

## Acesso, evidências e relatórios

O administrador envia um convite em POST /api/convites com email, empresa_id e role opcional. O destinatário usa o código recebido em POST /api/convites/aceitar com token, nome e senha. O código vale 72 horas. Recuperação de senha usa POST /api/autenticacao/recuperar-senha com email e POST /api/autenticacao/redefinir-senha com token e senha, dentro de uma hora. Configure SMTP_HOST e SMTP_FROM no .env. Para autenticação use SMTP_USER e SMTP_PASSWORD. SMTP_PORT usa 587 e SMTP_STARTTLS usa 1 por padrão. O login permite 20 tentativas por endereço IP em cinco minutos.

O gestor anexa um link HTTP(S) ou um arquivo de até 10 MiB à resposta em andamento. O conteúdo fica no PostgreSQL e o acesso exige permissão de leitura da avaliação. Administradores consultam as últimas 100 alterações em GET /api/auditoria.

Para relatórios configure AI_API_KEY e AI_MODEL no .env. AI_ENDPOINT aceita um provedor compatível com chat completions. O worker envia apenas o resultado consolidado. Defina AI_REPORT_LIMIT para ajustar o teto padrão de dez solicitações por avaliação. Cada solicitação gera um registro independente, inclusive em caso de falha. Consulte o estado e o texto pela listagem de relatórios da avaliação. O PDF fica disponível após conclusão.

Execute o worker em um processo separado do Flask:
```powershell
$env:PYTHONPATH = 'src'
.venv\Scripts\python -m flask --app prismati.bootstrap.app_factory:create_app processar-relatorios --continuo
```
