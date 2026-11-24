# Configuração do PrusaSlicer para os moldes (ABS, Anycubic Chiron)

Vale para o **contramolde** de cada kit e para a **tampa universal**. Medido no PrusaSlicer 2.7 em 24/11/2026:
contramolde Natal Parte 1 ≈ 210 g, tampa ≈ 138 g (kit completo ≈ 350 g).
Nenhuma das duas peças precisa de suporte. Os arquivos já vêm na posição certa: não girar.

## Config. de impressão

### Camadas e perímetros
| Opção | Valor |
|---|---|
| Altura da camada | 0,28 mm |
| Altura da primeira camada | 0,3 mm |
| Perímetros | 2 |
| Camadas sólidas: Topo | 4 |
| Camadas sólidas: Base | 3 |

### Preenchimento
| Opção | Valor |
|---|---|
| Densidade | 10% |
| Padrão | Relâmpago (Lightning) |

### Saia e aba
| Opção | Valor |
|---|---|
| Saia: voltas | 1 |
| Saia: distância da aba/objeto | 3 mm |
| Tipo de aba | Somente aba externa |
| Largura da aba | 10 mm |
| Espaçamento de separação da borda | 0 mm |

### Material de suporte
| Opção | Valor |
|---|---|
| Gerar material de suporte | Desligado |

### Velocidade
| Opção | Valor |
|---|---|
| Primeira camada | 20 mm/s |

## Filamentos (ABS)

### Filamento
| Opção | Valor |
|---|---|
| Diâmetro | 1,75 mm |
| Densidade | 1,04 g/cm³ (só para o peso aparecer certo) |
| Temperatura do bico: primeira camada / demais | 250 °C / 245 °C |
| Temperatura da mesa: primeira camada / demais | 105 °C / 105 °C |

### Resfriamento
| Opção | Valor |
|---|---|
| Mantenha a ventoinha sempre ligada | Desligado |
| Ativar o resfriamento automático | Desligado (ventoinha desligada) |

### Avançado
- Compensação de encolhimento: o PrusaSlicer 2.7 não tem. Não faz falta: contramolde e tampa em ABS encolhem juntos.

## Fora do fatiador
- Mesa lavada com detergente e seca; cola bastão em camada fina se a peça soltar.
- Esperar uns 5 min com a mesa já quente antes de começar.
- Impressora coberta (caixa de papelão), sem vento. Cômodo ventilado, longe das pessoas (cheiro do ABS).
- Deixar a peça esfriar em cima da mesa, coberta, antes de tirar.

## Como salvar no PrusaSlicer (para não perder)
1. Em **Config. de impressão**, ajuste tudo acima e clique no ícone de **disquete** ao lado do nome do perfil.
   Dê o nome **"Molde Palco ABS 0,28"** e salve.
2. Em **Filamentos**, faça o mesmo: disquete, nome **"ABS Palco"**.
3. Na **Bandeja**, escolha esses dois perfis nas listas do lado direito antes de fatiar.
4. Para guardar uma cópia fora do programa: menu **Arquivo > Exportar > Exportar pacote de configurações**.
