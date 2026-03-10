from flask import Flask, request, jsonify, render_template_string
from fertilizer_advisor import get_recommendation

app = Flask(__name__)

HTML_FORM = """
<h2>🌱 Fertilizer Advisor Test</h2>
<form method="post" action="/fertilizer-advice">
Crop: <input name="crop" value="wheat"><br><br>
Stage: <input name="stage" value="tillering"><br><br>
Nitrogen: <input name="nitrogen" value="120"><br><br>
Phosphorus: <input name="phosphorus" value="14"><br><br>
Potassium: <input name="potassium" value="80"><br><br>
Moisture: <input name="moisture" value="good"><br><br>
Latitude: <input name="lat" value="23.2"><br><br>
Longitude: <input name="lon" value="72.6"><br><br>
<button type="submit">Get Advice</button>
</form>
"""

@app.route("/")
def home():
    return render_template_string(HTML_FORM)

@app.route("/fertilizer-advice", methods=["POST"])
def fertilizer_advice():
    data = request.form

    result = get_recommendation(
        crop=data["crop"],
        stage=data["stage"],
        nitrogen_value=float(data["nitrogen"]),
        phosphorus_value=float(data.get("phosphorus", 0)),
        potassium_value=float(data.get("potassium", 0)),
        moisture=data["moisture"],
        lat=float(data["lat"]),
        lon=float(data["lon"])
    )

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
