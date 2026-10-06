# sbsr2027-precip-analysis

# Validação Espacial do GPM IMERG V07 no Cerrado: Efeito da Altitude nos Vieses de Precipitação em Goiás

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Event: SBSR](https://img.shields.io/badge/Presented%20at-SBSR-green.svg)](https://eventos.inpe.br/)

Este repositório contém o pipeline computacional e as rotinas de análise desenvolvidas para o artigo submetido no **XXII Simpósio Brasileiro de Sensoriamento Remoto (SBSR)**.

> **Autores:** [Marco Antônio dos Santos], [Klebber Teodomiro Martins Formiga]
> 
> **Instituição:** Programa de Pós-Graduação em Ciências Ambientais - Universidade Federal de Goiás (UFG)
> 
> **Contato:** [marco.antonio@discente.ufg.br]

---

## 📌 Visão Geral (Overview)

Este estudo avaliou o desempenho do produto de precipitação diária GPM IMERG V07 (versão final) frente a 43 estações pluviométricas do CEMADEN no estado de Goiás, no período de 2021 a 2025. A base pareada totalizou 71.253 pares diários. O IMERG apresentou correlação moderada (r = 0,63, ρ = 0,77) e leve subestimação (PBIAS = -5.4%), com bom desempenho na detecção de dias chuvosos (POD = 0,89 para ≥ 1 mm/dia), mas limitações em eventos extremos (POD = 0,13, para ≥ 50 mm). O desempenho foi melhor na primavera (KGE = 0,58) e pior no inverno. Observou-se subestimação crescente com a altitude (ρ = −0,54). Recomenda-se correção de viés para aplicações que exijam precisão absoluta.

---

## 🗺️ Principais Resultados (Highlights)


A avaliação do **GPM IMERG V07** frente às estações pluviométricas do **CEMADEN** para o estado de Goiás revelou:

* **Desempenho Geral Moderado:** Métricas globais diárias consistentes com $r = 0{,}63$, $\text{KGE} = 0{,}54$ e leve subestimação geral ($\text{PBIAS} = -5{,}4\%$).
* **Sensibilidade a Eventos Extremos:** Alta capacidade de detecção para baixos limiares pluviométricos, porém com queda expressiva em eventos severos ($\text{POD} = 0{,}13$ para precipitações $\ge 50\text{ mm/dia}$).
* **Variabilidade Sazonal & Espacial:** Desempenho superior durante a primavera e menor acurácia no período seco.
* **Efeito Orográfico:** Forte correlação entre altitude e viés volumétrico ($\rho_{\text{PBIAS}} = -0{,}54$), com subestimação acentuada em cotas elevadas.

> **Recomendação Prática:** O IMERG V07 é adequado como dado complementar para modelagem hidrológica regional em Goiás, mas requer rotinas prévias de **correção de viés (*bias correction*)** quando aplicado à estimativa de extremos pluviométricos ou bacias de relevo acidentado.

---

<p align="center">
  <img src="figures/validacao_imerg_cemaden.png" alt="Validação Espacial e Métricas do IMERG V07 em Goiás" width="800px"/>
  <br>
  <em>Figura 1: Distribuição espacial das métricas de desempenho (r, KGE, PBIAS) e influência topográfica na validação do GPM IMERG V07 com dados CEMADEN.</em>
</p>

---
