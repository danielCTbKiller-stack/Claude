# Diâmetros comerciais internos comuns para tubos de PVC predial (mm)
COMMERCIAL_DIAMETERS = [15, 20, 25, 32, 40, 50, 60, 75, 85, 110]

# Tabela padrão de aparelhos sanitários e pesos (NBR 5626)
FIXTURE_DATABASE = {
    "chuveiro_eletrico": {"weight": 0.4, "min_pressure": 1.0},
    "bacia_sanitaria_cx_acoplada": {"weight": 0.3, "min_pressure": 0.5},
    "lavatorio": {"weight": 0.1, "min_pressure": 0.5},
    "pia_cozinha": {"weight": 0.7, "min_pressure": 0.5},
    "maquina_lavar": {"weight": 1.0, "min_pressure": 1.0},
}

# Comprimentos equivalentes de conexões em tubo de PVC soldável (m), por diâmetro nominal (mm).
# Valores típicos de tabelas de fabricante (NBR 5626, anexo). Confira com a tabela do fabricante
# adotado no projeto; para diâmetros fora da faixa usa-se o valor da extremidade mais próxima e,
# entre dois diâmetros, interpola-se linearmente.
EQUIVALENT_LENGTH_DIAMETERS = [20, 25, 32, 40, 50, 60, 75, 85, 110]
EQUIVALENT_LENGTH_TABLE = {
    "joelho_90":          [1.1, 1.2, 2.0, 3.2, 3.4, 3.7, 3.9, 4.3, 4.9],
    "joelho_45":          [0.4, 0.5, 0.7, 1.0, 1.3, 1.5, 1.7, 1.8, 1.9],
    "te_passagem_direta": [0.7, 0.8, 0.9, 1.5, 2.2, 2.3, 2.4, 2.5, 2.6],
    "te_saida_lateral":   [2.3, 2.4, 3.1, 4.6, 7.3, 7.6, 7.8, 8.0, 8.3],
    "te_saida_bilateral": [2.3, 2.4, 3.1, 4.6, 7.3, 7.6, 7.8, 8.0, 8.3],
    "registro_gaveta":    [0.1, 0.2, 0.2, 0.3, 0.4, 0.4, 0.5, 0.5, 0.7],
    "registro_globo":     [11.4, 15.0, 22.0, 35.8, 37.9, 38.0, 40.0, 42.3, 50.9],
}
FITTING_LABELS = {
    "joelho_90": "joelho 90°", "joelho_45": "joelho 45°", "te_passagem_direta": "tê, passagem direta",
    "te_saida_lateral": "tê, saída lateral", "te_saida_bilateral": "tê, saída bilateral",
    "registro_gaveta": "registro de gaveta", "registro_globo": "registro de globo",
}
