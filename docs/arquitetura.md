# Arquitetura do PrismaTI

## Objetivo

O backend será uma aplicação modular em Python com Flask, organizada em Clean Architecture. O domínio e os casos de uso deverão funcionar sem depender de Flask, banco de dados ou provedor de IA.

O escopo inicial contempla empresas, usuários, convites, questionários versionados, avaliações, respostas, evidências, resultados, relatórios de IA e auditoria. Cada usuário empresarial pertence a uma única empresa no MVP, por meio de `company_id` em usuário.

Este documento descreve a arquitetura alvo. A implementação atual inclui CRUDs com Flask, SQLAlchemy Core, PostgreSQL/psycopg e Alembic. Consulte `api.md` para os endpoints e módulos pendentes. Os CRUDs compartilham o contrato Catalog e a implementação SqlCatalog; os contratos especializados anteriores permanecem disponíveis para evolução.

## Estrutura de pastas

```text
PrismaTI/
|-- README.md
|-- docs/
|   `-- arquitetura.md
|-- src/
|   `-- prismati/
|       |-- domain/
|       |   |-- entities/
|       |   |-- value_objects/
|       |   |-- enums/
|       |   |-- services/
|       |   `-- exceptions/
|       |-- application/
|       |   |-- use_cases/
|       |   |   |-- auth/
|       |   |   |-- companies/
|       |   |   |-- users/
|       |   |   |-- invitations/
|       |   |   |-- questionnaires/
|       |   |   |-- assessments/
|       |   |   |-- evidences/
|       |   |   |-- results/
|       |   |   `-- reports/
|       |   |-- ports/
|       |   |   `-- repositories/
|       |   `-- dto/
|       |-- presentation/
|       |   `-- http/
|       |       |-- blueprints/
|       |       |-- schemas/
|       |       |-- presenters/
|       |       |-- decorators/
|       |       `-- error_handlers/
|       |-- infrastructure/
|       |   |-- persistence/
|       |   |   |-- models/
|       |   |   |-- repositories/
|       |   |   `-- mappers/
|       |   |-- security/
|       |   |-- mail/
|       |   |-- storage/
|       |   |-- ai/
|       |   |-- jobs/
|       |   |-- pdf/
|       |   `-- observability/
|       `-- bootstrap/
|-- migrations/
`-- tests/
    |-- unit/
    |   |-- domain/
    |   `-- application/
    |-- integration/
    |-- http/
    `-- architecture/
```

## Responsabilidade de cada camada

### Domain: regras do negócio

- `entities/`: entidades como Empresa, Usuario, Avaliacao, Pergunta, Resposta e Resultado. São objetos Python, sem herdar de modelos de ORM.
- `value_objects/`: valores com validação própria, quando necessário, como CNPJ e pontuação.
- `enums/`: perfis, estados da avaliação, tipos de resposta e tipos de evidência.
- `services/`: regras que envolvem mais de uma entidade, como cálculo de maturidade, cobertura e suficiência do diagnóstico.
- `exceptions/`: erros de negócio independentes de códigos HTTP.

Não importa Flask, ORM, clientes HTTP de provedores ou módulos das camadas externas. Não acessa `request`, `current_app` ou sessão do banco.

### Application: casos de uso e contratos

- `use_cases/`: coordena operações como iniciar avaliação, salvar resposta, finalizar avaliação e solicitar relatório.
- `ports/repositories/`: contratos dos repositórios necessários aos casos de uso.
- `ports/`: demais contratos, como unidade de trabalho/transação, hash de senha, tokens, envio de e-mail, arquivos privados, IA, fila, exportação de PDF e auditoria.
- `dto/`: estruturas Python de entrada e saída dos casos de uso, sem objetos de Flask ou ORM.

Essa camada valida a autorização de negócio: empresa do usuário, perfil, gestor responsável e estado do recurso. Recebe a identidade do usuário autenticado explicitamente. As verificações não podem existir apenas em decorators HTTP, pois tarefas assíncronas também executam casos de uso.

Os contratos podem usar `typing.Protocol` ou classes abstratas. As implementações são recebidas pelo construtor; os casos de uso não criam clientes externos nem repositórios concretos.

### Presentation: entrada e saída HTTP com Flask

- `blueprints/`: rotas agrupadas por recurso, como autenticação, empresas, questionários, avaliações, evidências, resultados e relatórios.
- `schemas/`: validação do formato dos dados HTTP e conversão para DTOs. Regras de negócio permanecem nas camadas internas.
- `presenters/`: conversão das saídas dos casos de uso em respostas JSON e códigos HTTP.
- `decorators/`: autenticação da requisição e verificações preliminares de acesso.
- `error_handlers/`: tradução centralizada dos erros conhecidos para respostas padronizadas.

Uma rota recebe a requisição, obtém a identidade autenticada, valida o formato, chama um caso de uso e apresenta a resposta. Não calcula maturidade, consulta ORM diretamente ou chama o provedor de IA.

### Infrastructure: detalhes técnicos

- `persistence/models/`: modelos de persistência e mapeamento das tabelas do banco.
- `persistence/repositories/`: implementações dos contratos de repositório definidos na aplicação.
- `persistence/mappers/`: conversão entre registros persistidos e objetos do domínio.
- `persistence/`: também abriga a configuração de sessões e a implementação da unidade de trabalho.
- `security/`: hash de senha e mecanismos de autenticação e tokens.
- `mail/`: implementação do envio de convites e recuperação de acesso.
- `storage/`: armazenamento e recuperação privada das evidências.
- `ai/`: integração com o provedor, preparação técnica das chamadas e validação da estrutura retornada.
- `jobs/`: integração com a fila e entrada do worker, que chama os casos de uso de relatórios.
- `pdf/`: implementação da exportação dos relatórios.
- `observability/`: logs técnicos, rastreamento e integração da auditoria com os contratos da aplicação.

O banco, o ORM, a fila e os provedores externos ainda serão escolhidos. A arquitetura reserva os locais para suas implementações sem fixar essas escolhas.

### Bootstrap: montagem da aplicação

É o ponto de composição autorizado a conhecer as camadas concretas. Planejamento dos arquivos:

- `app_factory.py`: função `create_app`, responsável por criar o Flask, carregar configuração, inicializar extensões e registrar Blueprints e tratadores de erro.
- `container.py`: instancia repositórios e serviços concretos e os injeta nos casos de uso.
- `config.py`: configurações por ambiente obtidas externamente, sem credenciais no código.
- `extensions.py`: objetos de extensões Flask, quando adotadas, inicializados na fábrica com `init_app`.
- `wsgi.py`: ponto de entrada HTTP que expõe a aplicação criada pela fábrica.
- `worker.py`: montagem do processo de tarefas assíncronas com as mesmas regras da aplicação.

Não contém regras de negócio. As dependências concretas são montadas aqui, sem importar o container dentro do domínio ou dos casos de uso.

## Direção das dependências

```text
presentation   ---> application ---> domain
infrastructure ---> application ---> domain
bootstrap      ---> monta as implementações e os pontos de entrada
```

As setas representam dependências de código. A aplicação chama contratos; a infraestrutura implementa esses contratos. O fluxo de execução pode chegar ao banco, mas a aplicação não importa o repositório concreto.

## Exemplo de fluxo: salvar resposta

1. O Blueprint recebe a requisição de salvamento.
2. A apresentação valida o formato e monta um DTO com a identidade autenticada.
3. O caso de uso consulta avaliação e pergunta pelos contratos de repositório.
4. Valida empresa, gestor responsável, versão, alternativa e estado da avaliação.
5. O domínio aplica as regras da resposta.
6. O repositório concreto salva a alteração dentro da unidade de trabalho.
7. O caso de uso retorna um DTO, convertido em resposta HTTP pela apresentação.

## Regras estruturais do PrismaTI

- A finalização deve validar respostas, calcular resultados e alterar o estado da avaliação em uma única transação. Salvamentos e finalização devem usar controle de concorrência compatível para impedir alterações após o fechamento.
- A persistência deve garantir uma avaliação em andamento por empresa e uma resposta por pergunta em cada avaliação, inclusive sob concorrência.
- O vínculo entre empresa, gestor, avaliação, pergunta, versão e alternativa deve ser validado. Consultas empresariais devem respeitar o escopo autorizado.
- Versões publicadas são preservadas. Mudanças no instrumento geram outra versão, sem alterar avaliações anteriores.
- NA, NS e nota zero são valores distintos. As regras de cálculo pertencem ao domínio; a aplicação coordena seu armazenamento.
- Solicitar relatório registra uma tarefa persistida. O envio à fila deve permitir recuperação em caso de falha, por mecanismo como outbox ou consumo de tarefas persistidas.
- O worker executa a geração de forma independente da requisição HTTP. Novas tentativas devem ter controle de concorrência e idempotência.
- A IA interpreta resultados oficiais; não os calcula ou altera. Cada nova geração concluída preserva as versões anteriores do relatório.
- A aplicação verifica limites de consumo e registra uso por tentativa, quando informado pelo provedor, inclusive quando houver falha posterior na validação do retorno.
- Evidências ficam em armazenamento privado. O banco mantém seus metadados. Os anexos não são enviados automaticamente à IA no MVP.
- Recomendações, plano de ação e roadmap podem integrar o conteúdo estruturado e versionado do relatório; não exigem módulos de execução de ações no MVP.
- Auditoria registra operações relevantes sem expor senhas, tokens ou conteúdo confidencial desnecessário.

## Organização dos testes futuros

- `unit/domain/`: regras de resposta, fórmulas, cobertura e classificação, sem banco ou Flask.
- `unit/application/`: casos de uso com contratos substituídos por implementações de teste.
- `integration/`: persistência, transações, concorrência, isolamento por empresa e integrações externas.
- `http/`: contratos da API, autenticação, serialização e tradução de erros.
- `architecture/`: verificação de que domínio e aplicação não importam Flask nem infraestrutura.

As migrações de banco ficam em `migrations/`. Ainda não foram geradas, pois o modelo físico e a ferramenta de persistência serão definidos na implementação.

## Referências do Flask

- [Application Factories](https://flask.palletsprojects.com/en/stable/patterns/appfactories/)
- [Modular Applications with Blueprints](https://flask.palletsprojects.com/en/stable/blueprints/)
