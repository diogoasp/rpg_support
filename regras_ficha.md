A implementação deve separar três coisas:

1. **catálogo de opções do livro**;
2. **regras que aplicam efeitos dessas opções**;
3. **estado da criação**, que controla o que ainda pode ou não ser selecionado.

A fonte normativa é exclusivamente o [OP RPG — Livro do Jogador 1.5.7](sandbox:/mnt/data/OP%20RPG%20-%20Livro%20do%20Jogador%201.5.7.pdf), especialmente os capítulos 1 a 5 e 8.

---

# 1. Ordem oficial de criação

O fluxo apresentado no livro é:

1. escolher a espécie;
2. escolher o estilo de combate;
3. escolher a profissão;
4. determinar os atributos;
5. descrever e personalizar o personagem:

   * antecedente;
   * sonho;
   * caminho;
   * singularidades;
   * defeitos;
   * código de honra, quando houver;
6. escolher ou receber o equipamento;
7. calcular os valores derivados.

Referência: Livro do Jogador, pp. 8–12.

Para a aplicação, recomendo esta sequência operacional:

```text
1. Conceito básico
2. Espécie
3. Estilo de Combate
4. Profissão
5. Atributos
6. Antecedente
7. Personalidade
8. Proficiências e escolhas pendentes
9. Equipamento
10. Revisão e confirmação
```

A etapa “Proficiências e escolhas pendentes” é importante porque espécie, estilo, profissão e antecedente podem abrir escolhas adicionais.

---

# 2. Atributos

O sistema possui seis atributos:

* Força;
* Destreza;
* Constituição;
* Sabedoria;
* Vontade;
* Presença.

Não usar Inteligência ou Carisma do D&D tradicional.

## Geração

O livro oferece dois métodos:

### Conjunto padrão

```text
15, 14, 13, 12, 10, 8
```

Cada valor deve ser atribuído uma única vez.

### Aleatório

Para cada atributo:

```text
rolar 4d6
descartar o menor resultado
somar os três maiores
repetir seis vezes
```

A aplicação pode oferecer os dois métodos, mas não deve misturá-los na mesma criação.

## Modificador

```python
modifier = (attribute_value - 10) // 2
```

## Limite inicial

Os ajustes de espécie e antecedente não podem elevar um atributo acima de 20 durante a criação.

Referência: pp. 9–10 e 14.

## Regra de interface

Enquanto os seis valores básicos não forem distribuídos:

* os ajustes raciais podem ser selecionados;
* o resultado final pode ser pré-visualizado;
* a ficha não pode ser concluída.

A aplicação deve armazenar separadamente:

```text
valor_base
bônus_de_espécie
bônus_de_antecedente
outros_bônus
valor_final
```

Não grave apenas o valor final, pois isso dificulta auditoria e reconstrução da ficha.

---

# 3. Espécies

O livro apresenta:

* Anões;
* Celestiais;
* Gigantes;
* Humanos;
* Lunarianos;
* Mestiços;
* Minks;
* Povo do Mar.

Referência: Capítulo 2, pp. 13–30.

## Regra comum de atributos

Todas as espécies apresentadas usam:

```text
+2 em um atributo à escolha
ou
+1 em dois atributos diferentes à escolha
```

O valor final não pode ultrapassar 20.

O formulário deve usar escolha exclusiva:

```text
[ ] +2 em um atributo
[ ] +1 em dois atributos
```

Ao selecionar a primeira opção, mostrar um select.

Ao selecionar a segunda, mostrar dois selects que não podem repetir o mesmo atributo.

---

## 3.1 Anões

```text
PV base: 8
Tamanho: Miúdo
Deslocamento: 9 m
Nado: 4,5 m
Preconceito: Débil
```

Características essenciais:

* Corpo Pequeno;
* Estômago Pequeno;
* Piscar;
* Andar das Fadas;
* Hóspede Feérico;
* dificuldade Ingenuidade Anormal;
* traço cultural que concede Pontos de Treinamento conforme o modificador de Sabedoria.

Dependência importante:

```text
pontos_de_treinamento_iniciais =
máximo entre 1 e modificador positivo de Sabedoria
```

O texto também afirma que, com modificador negativo, o benefício não se torna disponível até que o modificador fique positivo. Essa aparente tensão deve ser preservada exatamente como regra cadastrada, sem o sistema tentar reinterpretá-la.

Após os atributos serem definidos, a aplicação deve recalcular os Pontos de Treinamento raciais e abrir a escolha de treinamentos compatíveis.

Referência: pp. 15–16.

---

## 3.2 Celestiais

```text
PV base: 10
Tamanho: Médio
Deslocamento: 12 m
Nado: 3 m
```

Deve ser obrigatória a escolha de uma variante:

* Birkan;
* Shandian;
* Skypean.

Efeitos das variantes:

```text
Birkan:
+5 em testes de Presença (Atuação)

Shandian:
+5 em testes de Força (Atletismo)

Skypean:
+5 em testes de Presença (Persuasão)
```

Também possuem:

* Herança Cultural ligada aos dials;
* escolha relacionada a dial inicial;
* Pontos de Treinamento derivados da Sabedoria, conforme o traço cultural.

Ao selecionar Celestial, o select de variante deve aparecer e ser obrigatório.

Referência: pp. 17–18.

---

## 3.3 Gigantes

```text
PV base: 20
Tamanho: Enorme
Deslocamento: 9 m
Nado: 3 m
```

Regras importantes para implementação:

* utilizam armas gigantescas;
* suas armas são incompatíveis com outras espécies;
* o equipamento inicial proveniente do estilo deve ser adaptado ao tamanho;
* efeitos relacionados a tamanho e alcance devem constar na ficha;
* limitações de espaço e equipamentos devem ser registradas como características.

Ao escolher Gigante, os selects de equipamentos devem buscar versões compatíveis com o tamanho do personagem.

Referência: pp. 19–20.

---

## 3.4 Humanos

```text
PV base: 10
Tamanho: Médio
Deslocamento: 9 m
Nado: 4,5 m
```

O humano deve escolher obrigatoriamente uma variante:

* Humano Comum;
* Humanozarrão;
* Tribo Braços Longos;
* Tribo Kuja;
* Tribo Pernas Longas;
* Tribo Pescoço de Cobra;
* Tribo dos Três Olhos.

### Humano Comum

* escolhe uma perícia;
* torna-se proficiente;
* dobra o bônus de proficiência nessa perícia.

Isso equivale a uma especialização funcional, mas deve ser armazenado com a terminologia do livro.

### Humanozarrão

* tamanho passa para Grande;
* recebe +2 em Salvaguardas de Força.

### Braços Longos

* alcance de 3 m em ataques corpo a corpo realizados com os braços;
* +2 em Destreza (Prestidigitação).

### Kuja

* recebe uma cobra companheira;
* abre as informações e capacidades da Cobra Bélica;
* o sistema deve permitir definir o nome da cobra;
* a cobra deve ser cadastrada como companheiro associado, não como item.

### Pernas Longas

* alcance de 3 m em ataques corpo a corpo realizados com as pernas;
* deslocamento normal passa para 12 m.

### Pescoço de Cobra

* alcance de 3 m em ataques realizados com a cabeça;
* +2 em Vontade (Percepção) dependente de visão.

### Três Olhos

Escolhe uma proficiência entre:

* Haki;
* Sobrenatural;
* Sorte.

A escolha deve abrir somente essas três opções.

Referência: pp. 21–23.

---

## 3.5 Lunarianos

```text
PV base: 16
Tamanho: Médio
Deslocamento: 9 m
Nado: 3 m
```

Possuem características raciais próprias relacionadas a:

* fisiologia lunariana;
* asas;
* fogo;
* resistência;
* mudança de estado conforme a chama;
* grande preconceito e perseguição.

Essas características devem ser cadastradas como efeitos passivos do personagem. Caso alguma delas tenha estado alternável, como chama ativa ou inativa, esse estado não pertence ao formulário de criação; pertence à ficha em uso.

Não há variante racial obrigatória indicada como nos humanos, celestiais, minks e povo do mar.

Referência: pp. 24–25.

---

## 3.6 Mestiços

A criação de mestiço depende de duas espécies ou duas variantes da mesma espécie.

### Derivações

```text
PV base:
média dos PV base das duas espécies, arredondada para baixo

Tamanho:
média dos menores valores das espécies, arredondada para baixo

Peso:
média dos maiores valores, arredondada para baixo

Deslocamento:
maior deslocamento das espécies

Nado:
maior deslocamento de nado
```

### Escolhas

* selecionar duas espécies de origem;
* escolher um benefício de cada espécie;
* escolher uma dificuldade entre as duas espécies;
* tratar ancestralidade ou traço cultural conforme as espécies;
* aplicar as regras específicas de treinamentos raciais.

### Mestiço de variantes da mesma espécie

* escolhe o benefício de cada variante;
* não recebe o benefício geral da espécie;
* não deve selecionar uma terceira variante.

O formulário não deve apresentar “Mestiço” como uma espécie isolada sem filiação. Ao escolhê-lo, devem aparecer:

```text
Espécie de origem A
Espécie de origem B
ou
Espécie única + Variante A + Variante B
```

As opções incompatíveis devem ser removidas dinamicamente.

Referência: pp. 26–27.

---

## 3.7 Minks

```text
PV base: 12
Tamanho: Pequeno, Médio ou Grande
Deslocamento: 9 m
Nado: 4,5 m
```

Variante obrigatória:

* Ágil;
* Meão;
* Robusto.

### Ágil

* deslocamento normal passa para 12 m;
* escalada passa para 9 m.

### Meão

* deslocamento normal passa para 18 m.

### Robusto

* deslocamento normal passa para 12 m;
* ignora redução por terreno difícil.

### Ancestralidade

O jogador deve informar o mamífero ancestral.

Depois escolhe:

* até dois Traços Comuns de Zoan;
* até um Traço Específico de Zoan;

desde que coerentes com o animal e aprovados pelo Narrador.

Alternativamente, se for um carnívoro caçador:

* pode abandonar todos esses traços;
* receber Predador.

O formulário precisa de uma escolha:

```text
Tipo de ancestralidade:
( ) Traços Zoan
( ) Predador
```

“Predador” só deve aparecer se o ancestral estiver marcado como carnívoro caçador ou se o mestre autorizar manualmente.

Também possuem Electro e a dificuldade Instintos Animalescos.

Referência: pp. 27–28 e regras Zoan do Capítulo 6.

---

## 3.8 Povo do Mar

```text
PV base: 14
Tamanho: Médio ou Grande
Deslocamento: 9 m
Nado: 15 m
```

Variante obrigatória:

* Homem-Peixe;
* Sireno.

### Homem-Peixe

* escolhe um Traço Comum de Zoan coerente com o animal marinho ancestral.

### Sireno

* nado passa para 18 m;
* pode usar Disparada como ação bônus enquanto nada.

### Ancestralidade

O jogador informa a criatura marinha ancestral e escolhe:

* até dois Traços Comuns;
* até um Traço Específico;

ou Predador, quando for carnívoro caçador.

Também possui a dificuldade Criatura do Mar, incluindo exigência aumentada de água.

Referência: pp. 29–30.

---

# 4. Estilos de Combate

O estilo determina:

* Dado de Vida;
* PV do estilo;
* salvaguardas;
* proficiências em equipamentos;
* proficiências em kits;
* opções de perícias;
* atributo primário;
* arma favorita;
* habilidade básica inata;
* equipamento inicial;
* progressão posterior.

Referência: Capítulo 3, pp. 31–104.

## Fórmula dos PV iniciais

```python
initial_hp = (
    maximum_hit_die_value
    + constitution_modifier
    + species_base_hp
)
```

O total mínimo de PV é 1.

O livro apresenta no texto introdutório essa soma, embora os blocos dos estilos mostrem o valor do dado mais Constituição. A implementação deve acrescentar o PV-base racial no cálculo final.

---

## Catálogo dos estilos no 1º nível

### Atirador

```text
Dado de Vida: d8
Salvaguardas: Destreza e Sabedoria
Perícias: escolha 3 quaisquer
Proficiências:
- armas de fogo;
- lançador de arpão;
- bazuca;
- canhão de mão;
- armas de navio;
- kit de abrir cadeado;
- kit de escalada;
- kit de primeiros socorros.

Atributo primário: Destreza
Arma favorita: pistola ou mosquete
Habilidade inata:
- Superioridade Absoluta;
- Aprendizado Excepcional.

Equipamento:
- 2 pistolas; ou
- 1 mosquete;
- 80 munições esféricas;
- 5d10 × 1.000 bellys.
```

### Carateca Homem-Peixe

```text
Dado de Vida: d12
Salvaguardas: Constituição e Força
Perícias: escolha 2 entre:
- Acrobacia;
- Atletismo;
- Atuação;
- Intimidação.

Atributo primário: Força
Arma favorita:
- tridente;
- Corporal.

Habilidade inata:
- Corpo de Guerreiro;
- Aprimoramento de Atributo.

Equipamento:
- uma arma marcial; ou
- 40.000 bellys;
- mais 15d10 × 1.000 bellys.
```

A aplicação deve validar requisitos raciais ou autorização do mestre conforme o texto completo do estilo.

### Ciborgue

```text
Dado de Vida: d12
Salvaguardas: Força e Sabedoria
Perícias: escolha 2 entre:
- Atletismo;
- Investigação;
- Prestidigitação;
- Sobrevivência.

Proficiência em equipamento: nenhuma
Atributo primário: Força ou Sabedoria
Arma favorita:
- bazuca;
- canhão de mão;
- escopeta;
- metralhadora.

Habilidade inata:
- Aprendizado Excepcional;
- Aprimoramento de Atributo.

Equipamento:
- 20 unidades de combustível;
- 10d10 × 1.000 bellys.
```

O estilo abre as escolhas de construção do corpo ciborgue previstas no capítulo. Essas escolhas devem ser tratadas como opções próprias do estilo.

### Espadachim

```text
Dado de Vida: d10
Salvaguardas: Destreza e Vontade
Perícias: escolha 2 entre:
- Atletismo;
- Intimidação;
- Intuição;
- Percepção.

Proficiência: armas cortantes
Atributo primário: Força ou Destreza
Arma favorita:
- qualquer arma cortante;
- espada montante.

Habilidade inata:
- Perito em Técnicas;
- Superando Limites.

Equipamento:
- 2 sabres; ou
- 2 katanas;
- 5d10 × 1.000 bellys.
```

### Guerreiro-Oni

```text
Dado de Vida: d12
Salvaguardas: Força e Constituição
Perícias: escolha 2 entre:
- Atletismo;
- Intimidação;
- Provocação;
- Sobrevivência.

Proficiência: kanabo/tacape
Atributo primário: Força
Arma favorita:
- kanabo;
- machado grande;
- martelo de guerra;
- espada montante;
- Corporal.

Habilidade inata:
- Corpo de Guerreiro;
- Superioridade Absoluta.

Equipamento:
- 1 kanabo;
- 6d10 × 1.000 bellys.
```

Requisitos específicos do estilo devem ser representados como pré-requisitos configuráveis.

### Guerrilheiro

```text
Dado de Vida: d10
Salvaguardas: Destreza e Força
Perícias: escolha 2 entre:
- Acrobacia;
- Atletismo;
- Furtividade;
- História;
- Sobrevivência.

Proficiências:
- armas cortantes;
- armas de fogo;
- armas especiais;
- armas marciais;
- kit de escalada;
- kit de primeiros socorros.

Atributo primário: Força ou Sabedoria
Arma favorita:
- qualquer arma;
- Corporal.

Habilidade inata:
- Corpo de Guerreiro;
- Aprendizado Excepcional.

Equipamento:
- 2 pistolas; ou
- 1 mosquete e munição; ou
- 2 armas cortantes;
- 5d10 × 1.000 bellys.
```

### Lutador

```text
Dado de Vida: d12
Salvaguardas: Constituição e Força
Perícias: escolha 2 entre:
- Atletismo;
- Intimidação;
- Provocação;
- Sobrevivência.

Proficiência: armas marciais
Atributo primário: Força
Arma favorita:
- uma arma marcial;
- Corporal.

Habilidade inata:
- Corpo de Guerreiro;
- Superando Limites.

Equipamento:
- uma arma marcial; ou
- 40.000 bellys;
- mais 15d10 × 1.000 bellys.
```

### Ninja

```text
Dado de Vida: d8
Salvaguardas: Destreza e Sabedoria
Perícias: escolha 2 entre:
- Acrobacia;
- Enganação;
- Furtividade;
- Prestidigitação.

Proficiências:
- katana;
- kunai;
- adaga;
- shuriken;
- foice;
- arco;
- kit de abrir cadeado;
- kit de disfarce;
- kit de escalada;
- kit de venenos.

Atributo primário: Destreza
Arma favorita:
- katana;
- kunai;
- adaga;
- shuriken;
- foice;
- arco.

Habilidade inata:
- Defesa Ofensiva;
- Sortudo.

Equipamento:
- 1 katana;
- 5 kunais;
- 30 shurikens;
- 6d10 × 1.000 bellys.
```

### Okama Kenpo

```text
Dado de Vida: d10
Salvaguardas: Destreza e Presença
Perícias: escolha 3 entre:
- Acrobacia;
- Atletismo;
- Atuação;
- Enganação;
- Intimidação;
- Intuição;
- Provocação.

Proficiência: armas marciais
Atributo primário: Força ou Presença
Arma favorita:
- uma arma marcial;
- Corporal.

Habilidade inata:
- Corpo de Guerreiro;
- Superando Limites.

Equipamento:
- uma arma marcial; ou
- 40.000 bellys;
- mais 15d10 × 1.000 bellys.
```

### Usuário de Rokushiki

```text
Dado de Vida: d10
Salvaguardas: Destreza e Força
Perícias: escolha 2 entre:
- Acrobacia;
- Atletismo;
- Enganação;
- Furtividade;
- História;
- Investigação.

Proficiências:
- armas marciais;
- kit de abrir cadeado;
- kit de disfarce;
- kit de falsificação.

Atributo primário: Força ou Destreza
Arma favorita:
- adaga;
- katana;
- bastão;
- Corporal.

Habilidade inata:
- Corpo de Guerreiro;
- Perito em Técnicas.

Equipamento:
- uma arma marcial; ou
- 40.000 bellys;
- mais 15d10 × 1.000 bellys.
```

---

# 5. Profissões

Profissões principais:

* Adestrador;
* Arqueólogo;
* Caçador de Recompensas;
* Carpinteiro;
* Combatente;
* Cozinheiro;
* Engenheiro;
* Médico;
* Músico;
* Navegador.

Timoneiro é apresentado como **subprofissão de Navegador**, não como profissão principal independente.

Também é permitido escolher **Não ter profissão**.

Referência: Capítulo 4, pp. 105–134.

## Regras gerais

Uma profissão principal concede:

* escolha de duas perícias dentro de sua lista;
* Perícia Especial do Ofício;
* ferramentas;
* itens iniciais;
* Conhecimentos do Trabalho.

Profissão auxiliar não concede novamente as perícias e itens da profissão principal.

---

## Catálogo das profissões

### Adestrador

```text
Perícias: escolha 2 entre:
Acrobacia, Atuação, Intuição, Percepção, Persuasão, Sobrevivência.

Perícia Especial: Lidar com Animais
Ferramenta: Ferramentas de Adestrador
Itens:
- ferramentas de adestrador amador;
- mochila pequena;
- 30 rações para animais.
```

### Arqueólogo

```text
Perícias:
História, Intuição, Investigação, Percepção, Persuasão, Sobrevivência.

Perícia Especial: História Perdida
Itens:
- ferramentas de arqueólogo amador;
- mochila pequena;
- lanterna;
- corda;
- tenda.
```

### Caçador de Recompensas

```text
Perícias:
Furtividade, Intimidação, Investigação, Percepção, Persuasão, Sobrevivência.

Perícia Especial: Caça
Itens:
- ferramentas de caçador de recompensas amador;
- mochila pequena.
```

### Carpinteiro

```text
Perícias:
Acrobacia, Atletismo, História, Investigação, Persuasão, Prestidigitação.

Perícia Especial: Carpintaria
Itens:
- ferramentas de carpinteiro amador;
- mochila pequena.
```

### Combatente

```text
Perícias:
Acrobacia, Atletismo, Furtividade, Intimidação, Provocação, Sobrevivência.

Perícia Especial: Noção de Batalha
Itens:
- ferramentas de combatente amador;
- mochila pequena.
```

### Cozinheiro

```text
Perícias:
Atuação, Intuição, Persuasão, Prestidigitação, Provocação, Sobrevivência.

Perícia Especial: Gastronomia
Itens:
- ferramentas de cozinheiro amador;
- mochila pequena.
```

### Engenheiro

```text
Perícias:
História, Intuição, Investigação, Percepção, Prestidigitação, Sobrevivência.

Perícia Especial: Engenharia
Itens:
- ferramentas de engenheiro amador;
- mochila pequena.
```

### Médico

```text
Perícias:
História, Intuição, Investigação, Percepção, Prestidigitação, Sobrevivência.

Perícia Especial: Medicina
Itens:
- ferramentas de médico amador;
- mochila pequena.
```

### Músico

```text
Perícias: escolha 2 entre:
Acrobacia, Atuação, Enganação, Furtividade, Intimidação,
Intuição, Percepção, Persuasão, Prestidigitação e Provocação.

Perícia Especial: Canção
```

Os instrumentos e itens devem seguir o bloco da profissão no livro.

### Navegador

```text
Perícias:
Enganação, Intuição, Investigação, Percepção, Persuasão, Sobrevivência.

Perícia Especial: Navegação
Itens:
- ferramentas de navegador amador;
- mochila pequena.
```

### Timoneiro

Só deve aparecer se:

```text
profissão principal == Navegador
```

Ele permite substituir um ou mais Conhecimentos do Trabalho de Navegador por conhecimentos de Timoneiro.

### Sem profissão

Concede:

* Ajudante Perfeito;
* proficiência em duas perícias livres, exceto:

  * Haki;
  * Sobrenatural;
  * Sorte;
* Parceiro de Treino;
* Tempo Livre.

A escolha “Sem profissão” deve ocultar todas as profissões auxiliares e impedir sua aquisição posterior, conforme a regra do livro.

---

# 6. Antecedentes

Antecedentes disponíveis:

* Artista;
* Criminoso;
* Escravo;
* Família D.;
* Marinheiro;
* Nobre;
* Órfão;
* Político;
* Revolucionário;
* Sacerdote;
* Sobrevivente;
* Tenryuubito.

Referência: pp. 144–147.

Cada antecedente concede:

* proficiência em duas perícias da lista;
* aumento de atributo;
* uma característica especial.

O atributo indicado pelo livro é **recomendado**, não obrigatório.

A implementação deve permitir:

```text
+2 em um atributo
ou
+1 em dois atributos
```

respeitando o limite de 20.

## Listas de perícias

```text
Artista:
Acrobacia, Atuação, História, Persuasão, Prestidigitação, Provocação.
Recomendado: Presença.

Criminoso:
Enganação, Furtividade, Intimidação, Prestidigitação.
Recomendado: Destreza.

Escravo:
Atletismo, Intuição, Percepção, Sobrevivência.
Recomendado: Constituição.

Família D.:
Haki, Intimidação, Intuição, Percepção.
Recomendado: Vontade.

Marinheiro:
Acrobacia, Atletismo, Investigação, Sobrevivência.
Recomendado: Força.

Nobre:
usar exatamente a lista integral apresentada no bloco do antecedente.
Recomendação conforme o livro.

Órfão:
Atletismo, Furtividade, Intuição, Sobrevivência.
Recomendado: Força.

Político:
Atuação, Enganação, História, Intuição, Persuasão, Provocação.
Recomendado: Presença.

Revolucionário:
Acrobacia, Atletismo, História, Persuasão.
Recomendado: Destreza.

Sacerdote:
História, Percepção, Persuasão, Sobrenatural.
Recomendado: Sabedoria.

Sobrevivente:
História, Intuição, Percepção, Sobrevivência.
Recomendado: Vontade.

Tenryuubito:
História, Intimidação, Investigação, Natureza.
Recomendado: Constituição.
```

O livro permite personalizar um antecedente:

* trocar sua característica especial;
* escolher outras duas perícias;
* trocar o atributo;
* criar um antecedente com aprovação do Narrador.

Por isso, o sistema precisa de:

```text
modo padrão
modo personalizado pelo mestre
```

Jogadores não devem personalizar livremente sem aprovação.

---

# 7. Perícias gerais

## Força

* Atletismo.

## Destreza

* Acrobacia;
* Furtividade;
* Prestidigitação.

## Sabedoria

* História;
* Investigação;
* Natureza;
* Sobrevivência.

## Presença

* Atuação;
* Enganação;
* Intimidação;
* Persuasão;
* Provocação.

## Vontade

* Haki;
* Intuição;
* Percepção;
* Sobrenatural;
* Sorte.

Constituição não possui perícias gerais no modelo da ficha.

Referência: Capítulo 9, pp. 226–234, e Anexo A.

## Bônus

```python
skill_bonus = attribute_modifier
```

Se proficiente:

```python
skill_bonus += proficiency_bonus
```

Se o efeito dobrar a proficiência:

```python
skill_bonus += proficiency_bonus * 2
```

O bônus de proficiência não pode ser somado duas vezes por fontes comuns. Uma fonte de especialização substitui o uso normal, não soma normal + dobrado.

---

# 8. Sobreposição de proficiências

Uma mesma perícia pode ser concedida por:

* espécie;
* estilo;
* profissão;
* antecedente;
* treinamento.

O sistema não pode simplesmente descartar escolhas repetidas sem informar o jogador.

Quando uma fonte permite escolher e a perícia já foi adquirida por outra fonte:

* ocultar a opção repetida, quando o texto exige uma nova proficiência;
* ou permitir a seleção somente se a fonte transformar a proficiência em proficiência dobrada;
* mostrar de qual fonte cada proficiência veio.

Modelo recomendado:

```text
CharacterProficiency
- character
- proficiency
- source_type
- source_id
- multiplier
- is_choice
```

---

# 9. Valores derivados

## Bônus de proficiência

No 1º nível:

```text
+2
```

Deve ser derivado da progressão do estilo, não digitado manualmente.

## Classe de Resistência

Padrão:

```python
resistance_class = 10 + dexterity_modifier
```

Características podem substituir ou modificar esse cálculo.

O sistema deve trabalhar com fórmulas priorizadas:

```text
fórmula base
fórmula substitutiva
bônus aditivos
```

Exemplo: Corpo de Guerreiro pode substituir a fórmula padrão.

## PV

```python
maximum_hp = (
    hit_die_maximum
    + constitution_modifier
    + species_base_hp
    + other_modifiers
)
```

## Ataques

Corpo a corpo:

```python
attack_bonus = strength_modifier + proficiency_bonus
damage_bonus = strength_modifier
```

Arma com Acuidade:

```text
Força ou Destreza
```

Ataque à distância:

```text
Destreza
```

Arma com Arremesso:

```text
pode usar Força
```

Só somar proficiência se o personagem for proficiente com a arma.

## Carga

```python
carrying_capacity = strength * 10
```

Referência: pp. 10–11.

---

# 10. Regras dinâmicas do formulário

O frontend nunca deve ser a única camada de validação. As mesmas regras precisam existir no backend.

## Espécie → variante

```text
Celestial → Birkan, Shandian, Skypean
Humano → sete variantes humanas
Mink → Ágil, Meão, Robusto
Povo do Mar → Homem-Peixe, Sireno
Mestiço → origens e benefícios derivados
```

Para Anão, Gigante e Lunariano, ocultar o campo variante quando não aplicável.

## Espécie → ancestralidade

```text
Mink → mamífero + traços Zoan
Povo do Mar → criatura marinha + traços Zoan
Humano Kuja → cobra companheira
Mestiço → ancestralidade conforme as origens
```

## Estilo → perícias

O número e a lista mudam conforme o estilo.

## Estilo → arma favorita

Mostrar somente armas permitidas pelo estilo.

## Estilo → habilidade básica

Mostrar apenas as duas opções oferecidas pelo estilo.

## Estilo → equipamento

Mostrar somente os pacotes válidos.

## Profissão → perícias e ferramenta

A profissão redefine:

* lista de duas perícias;
* Perícia Especial;
* ferramenta;
* itens.

## Navegador → Timoneiro

Só exibir opções de Timoneiro para Navegador.

## Sem profissão

Ao selecionar:

* ocultar profissões auxiliares;
* mostrar duas perícias livres;
* remover Haki, Sobrenatural e Sorte da lista.

## Antecedente → perícias

Mostrar apenas a lista correspondente, exceto em modo personalizado autorizado.

## Atributos → efeitos derivados

Alterar Constituição deve recalcular PV.

Alterar Destreza deve recalcular CR e iniciativa.

Alterar Sabedoria pode alterar Pontos de Treinamento raciais.

Alterar espécie pode invalidar:

* variante;
* tamanho;
* ancestralidade;
* equipamento;
* PV;
* treinamentos.

O sistema deve pedir confirmação antes de apagar escolhas dependentes.

---

# 11. Arquitetura recomendada para as regras

Não codificar tudo em grandes blocos `if/elif`.

Criar um catálogo versionado.

Entidades sugeridas:

```text
Species
SpeciesVariant
SpeciesTrait
SpeciesChoice
SpeciesChoiceOption

CombatStyle
CombatStyleSkillChoice
CombatStyleProficiency
CombatStyleEquipmentChoice
CombatStyleFeatureChoice

Profession
ProfessionSkillChoice
ProfessionSpecialSkill
ProfessionEquipment

Background
BackgroundSkillChoice
BackgroundFeature

AttributeBonusRule
Prerequisite
RuleEffect
CharacterCreationChoice
CharacterCreationValidation
```

Efeitos estruturados devem suportar:

```text
ADD_PROFICIENCY
DOUBLE_PROFICIENCY
ADD_ATTRIBUTE
SET_MOVEMENT
SET_SWIM_SPEED
SET_SIZE
ADD_SAVE_BONUS
ADD_SKILL_BONUS
ADD_FEATURE
ADD_EQUIPMENT
CREATE_COMPANION
REQUIRE_CHOICE
RESTRICT_OPTION
```

Descrições narrativas continuam em texto, mas modificadores calculáveis devem ser estruturados.

---