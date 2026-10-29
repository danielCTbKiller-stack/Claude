# Hydrosanitary backend

Motor de cálculo de água fria + importação de projetos.

## Importação (DXF e IFC)

```python
from importers import import_project
from importers.config import ImportConfig
from services.network_analyzer import NetworkAnalyzer

res = import_project("projeto.dxf", ImportConfig.from_json("config/import_config.json"))
out = NetworkAnalyzer(res.project).analyze(res.source_id, source_pressure_mca=5.0, auto_size=True)
print(res.warnings, out["alerts"])
```

### Padrão DXF (configurável em `config/import_config.json`)
| Elemento | Como desenhar |
|---|---|
| Tubo | LINE / LWPOLYLINE / POLYLINE na layer `AF_TUBO_<diâmetro mm>` (ex.: `AF_TUBO_25`); `AF_TUBO` = diâmetro padrão |
| Aparelho | bloco na layer `AF_APARELHO`, com nome = chave de `FIXTURE_DATABASE` (ex.: `chuveiro_eletrico`) ou apelido |
| Fonte de água | qualquer bloco na layer `AF_FONTE`, sobre uma ponta de tubo |
| Paredes | LINE / polilinha na layer `AF_PAREDE` (altura `wall_height_m`, padrão 2,7 m) |
| Cômodo | polilinha fechada na layer `AF_COMODO_<nome>`; aparelhos dentro do contorno pertencem ao cômodo |
| Cota | coordenada Z; unidade pelo `$INSUNITS` do arquivo (senão `default_unit`) |

Pontas a até `snap_tolerance_m` (5 cm) são unidas no mesmo nó. Aparelhos e fonte precisam estar sobre uma ponta de tubo.

### Padrão IFC
`IfcPipeSegment` = tubo (diâmetro de `NominalDiameter` ou da geometria); `IfcSanitaryTerminal` = aparelho
(`PredefinedType` SHOWER/TOILETPAN/WASHHANDBASIN/SINK, ou `ObjectType` = chave do aparelho);
fonte = elemento com "FONTE" no nome.

DWG: converta para DXF antes (ex.: ODA File Converter).

## Interface gráfica

```
pip install -r requirements.txt
python -m gui.app [projeto.dxf|projeto.ifc]
```
Abra o projeto (Ctrl+O), ajuste pressão da fonte / velocidade máxima, marque dimensionamento automático se quiser e calcule (F5).
A vista isométrica mostra pisos dos cômodos, paredes translúcidas e a tubulação por cima (há também a Planta e "Girar vista 90°"). Desmarque cômodos em "Cômodos consumindo" para simular uso simultâneo parcial. Os tubos aparecem em cinza quando não têm consumo. A planta mostra tubos coloridos pela velocidade (verde ok, azul baixa, vermelho acima do limite) e nós com a pressão; passe o mouse para ver detalhes. Roda do mouse = zoom.

Exemplo completo (casa com banheiro, cozinha e área de serviço): `python examples/make_sample_house.py casa.dxf`.

## Memorial de cálculo

Na interface: calcule e use Arquivo → Exportar memorial de cálculo (Ctrl+E), em PDF ou HTML. Contém dados de entrada, vista isométrica, método, aparelhos, dimensionamento dos trechos, verificação de pressões, alertas e quantitativo. Em código: `services.report_generator.generate_memorial(...)`. Exemplo: `examples/memorial_exemplo.pdf`.
