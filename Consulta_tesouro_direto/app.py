from flask import Flask, jsonify
from flask_cors import CORS
import requests
import csv
import io
from datetime import datetime

app = Flask(__name__)
CORS(app)

CSV_URL = (
    "https://www.tesourotransparente.gov.br/ckan/dataset/"
    "df56aa42-484a-4a59-8184-7676580c81e3/resource/"
    "796d2059-14e9-44e3-80c9-2d9e30b405c1/download/precotaxatesourodireto.csv"
)

CLASSIFICACAO = {
    "Tesouro Selic": "Pós-fixado",
    "Tesouro IPCA+": "Híbrido",
    "Tesouro IPCA+ com Juros Semestrais": "Híbrido",
    "Tesouro IGPM+ com Juros Semestrais": "Híbrido",
    "Tesouro Prefixado": "Prefixado",
    "Tesouro Prefixado com Juros Semestrais": "Prefixado",
    "Tesouro Renda+ Aposentadoria Extra": "Renda+",
    "Tesouro Educa+": "Educa+",
}


def parse_br_float(value):
    try:
        return float(value.replace(",", "."))
    except Exception:
        return None


def parse_br_date(value):
    try:
        return datetime.strptime(value.strip(), "%d/%m/%Y")
    except Exception:
        return None


@app.route("/api/titulos")
def titulos():
    resp = requests.get(CSV_URL, timeout=15)
    resp.encoding = "utf-8"

    reader = csv.DictReader(io.StringIO(resp.text), delimiter=";")
    rows = list(reader)

    # find most recent data date
    dates = [parse_br_date(r["Data Base"]) for r in rows if parse_br_date(r["Data Base"])]
    if not dates:
        return jsonify({"erro": "Sem dados disponíveis"}), 500
    ultima_data = max(dates)
    ultima_data_str = ultima_data.strftime("%d/%m/%Y")

    titulos = []
    for row in rows:
        if row["Data Base"].strip() != ultima_data_str:
            continue
        tipo = row["Tipo Titulo"].strip()
        titulos.append({
            "tipo": tipo,
            "classificacao": CLASSIFICACAO.get(tipo, "Outro"),
            "vencimento": row["Data Vencimento"].strip(),
            "taxa_compra": parse_br_float(row["Taxa Compra Manha"]),
            "taxa_venda": parse_br_float(row["Taxa Venda Manha"]),
            "pu_venda": parse_br_float(row["PU Venda Manha"]),
        })

    titulos.sort(key=lambda x: (x["classificacao"], x["tipo"], x["vencimento"]))

    return jsonify({
        "data_referencia": ultima_data_str,
        "total": len(titulos),
        "titulos": titulos,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
