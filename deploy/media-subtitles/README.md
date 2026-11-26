# Legendas de séries

Stack isolada para catalogar as séries existentes e gerenciar legendas externas usadas pelo Plex.

- Sonarr: catálogo somente; nenhum indexador ou cliente de download deve ser configurado.
- Bazarr: busca, gravação e sincronização de legendas em `/srv/midia/Séries`.
- Os dois serviços enxergam a biblioteca pelo mesmo caminho interno, `/tv`.
- Os painéis ficam restritos ao endereço LAN do servidor.
- Cada serviço está limitado a 512 MB de RAM e 1,5 CPU.

## Configuração aplicada

- Perfil padrão de séries: `Português (Brasil)` (`pt-BR`).
- Mapeamento de idioma: resultados marcados apenas como português são tratados
  como PT-BR. Isso é necessário porque várias fontes não distinguem `pt` de
  `pt-BR` nos metadados.
- Provedores sem conta: Gestdown, SubF2M e SubtitleCat.
- Traduções automáticas do SubtitleCat habilitadas como alternativa gratuita.
- Pontuação mínima para séries: 65%.
- Sincronização automática habilitada, incluindo correção de offset e de
  framerate.
- Uma busca manual não baixa nada; ela pode ser usada para conferir a fonte e
  a pontuação antes de escolher uma legenda.

O Sonarr foi mantido sem indexadores e sem cliente de download. Ele serve
somente para fornecer o catálogo ao Bazarr.

## Organização da biblioteca

Cada série precisa ter uma única pasta raiz para ser cadastrada no Sonarr. A
biblioteca atual também contém temporadas e episódios em pastas separadas por
release. Esses diretórios não devem ser importados automaticamente, pois o
Sonarr pode associá-los à série errada. Reorganize-os somente com uma operação
específica e revisada, sem mover arquivos durante a configuração desta stack.

## Operação

```bash
cd /home/diogo/media-subtitles
docker compose up -d
docker compose ps
docker compose logs --tail=100 sonarr bazarr
```

Interfaces:

- Sonarr: `http://192.168.18.178:8989`
- Bazarr: `http://192.168.18.178:6767`

