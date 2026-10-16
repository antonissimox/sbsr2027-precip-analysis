# Validação Espacial do GPM IMERG V07 no Cerrado: Efeito da Altitude nos Vieses de Precipitação em Goiás

Este repositório contém o pipeline computacional e as rotinas de análise desenvolvidas para o artigo submetido ao **XXII Simpósio Brasileiro de Sensoriamento Remoto (SBSR)**.

* **Autores:** Marco Antônio dos Santos, Klebber Teodomiro Martins Formiga
* **Instituição:** Programa de Pós-Graduação em Ciências Ambientais (PPGCIAMB) — Universidade Federal de Goiás (UFG)
* **Contato:** marco.antonio@discente.ufg.br

---

## 📌 Visão Geral (Overview)

Este estudo avaliou o desempenho do produto de precipitação diária **GPM IMERG Final Run V07** frente a **41 estações pluviométricas do CEMADEN** (critério duplo de completude temporal $\ge$ 80%) no estado de Goiás, no período de janeiro de 2021 a setembro de 2025. 

A base pareada totalizou **68.201 pares diários**. O produto apresentou correlação moderada ($r = 0{,}65$; $\text{KGE} = 0{,}57$) e leve subestimação geral ($\text{PBIAS} = -4{,}75\%$; $\text{RMSE} = 8{,}13\text{ mm/dia}$), com alta capacidade de detecção de chuvas fracas ($\text{POD} = 0{,}92$ para $\ge 0{,}1\text{ mm/dia}$), porém com sensibilidade reduzida para eventos extremos ($\text{POD} = 0{,}13$ para $\ge 50\text{ mm/dia}$). 

Identificou-se forte dependência orográfica: o viés volumétrico apresentou correlação inversa e estatisticamente significativa com a altitude ($r = -0{,}54$; $p = 0{,}002$), variando progressivamente de $+5{,}2\%$ (abaixo de 600 m) a $-14{,}8\%$ (acima de 1000 m).

---

## 🗺️ Principais Resultados (Highlights)

* **Desempenho Geral Moderado:** Concordância consistente na escala diária ($r = 0{,}65$; $R^2 = 0{,}43$; $\text{KGE} = 0{,}57$; $\text{RMSE} = 8{,}13\text{ mm/dia}$) com discreta subestimação global ($\text{PBIAS} = -4{,}75\%$).
* **Sensibilidade a Eventos Extremos:** Alta detecção em baixos limiares, mas subestimação expressiva dos picos pluviais (ajuste linear: $\text{sim} = 0{,}493 \cdot \text{obs} + 1{,}81$).
* **Assinatura Orográfica do Viés:** O $\text{PBIAS}$ decai de forma monotônica com o gradiente altimétrico ($r = -0{,}54$), enquanto a dispersão do erro ($\text{RMSE}$) permaneceu estável ($r = +0{,}01$).
* **Consistência Regional:** A agregação pelas 5 mesorregiões do IBGE confirmou maior subestimação nas mesorregiões mais elevadas (Leste Goiano: $-10{,}7\%$; Centro Goiano: $-5{,}8\%$) e superestimação em cotas baixas (Norte Goiano: $+6{,}7\%$).

---

## 📂 Estrutura do Repositório

```text
.
├── 00_download_imerg_earthdata.py  # Script de aquisição e recorte via NASA Earthdata
├── 01_validacao_sbsr2027.py       # Pipeline de validação, cálculo de métricas e figuras
├── requirements.txt                # Dependências do projeto
├── LICENSE                         # Licença MIT
└── README.md
