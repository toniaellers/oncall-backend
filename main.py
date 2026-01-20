from flask import Flask, jsonify, request, Response

app = Flask(__name__)

# ---------------------------
# Helpers
# ---------------------------

def twiml(xml: str) -> Response:
    """Return a TwiML (text/xml) response."""
    return Response(xml, mimetype="text/xml")

def twiml_say(lines) -> Response:
    """Return TwiML that says one or more lines."""
    if isinstance(lines, str):
        lines = [lines]
    body = "\n".join([f"  <Say>{line}</Say>" for line in lines])
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
{body}
</Response>
"""
    return twiml(xml)

# ---------------------------
# Basic health routes
# ---------------------------

@app.route("/")
def home():
    return "Nova is alive 🚀"

@app.route("/ping")
def ping():
    return jsonify({"status": "ok", "version": "v1-clean"})

@app.route("/routes")
def routes():
    return "<br>".join(sorted([str(r) for r in app.url_map.iter_rules()]))

# ---------------------------
# Twilio Voice: Entry point
# ---------------------------

@app.route("/incoming-call", methods=["GET", "POST"])
def incoming_call():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say>
    Hi! Thanks for calling OnCall Agency — this is Nova.
    We help businesses never miss a call, and never miss a job.
    A lot of important calls come in after hours or when business owners are busy,
    so I’m here to help.
  </Say>

  <Gather input="speech dtmf"
          timeout="5"
          numDigits="1"
          action="/handle-input"
          method="POST">
    <Say>
      Press 1 to schedule a quick call back.
      Press 2 to reschedule or cancel an appointment.
      Press 3 if you’re looking for a quote or more information.
      Or just tell me what you’re calling about.
    </Say>
  </Gather>

  <Say>Sorry, I didn’t hear anything. Goodbye.</Say>
</Response>
"""
    return twiml(xml)

# ---------------------------
# Twilio Voice: Menu routing
# ---------------------------

@app.route("/handle-input", methods=["POST"])
def handle_input():
    digit = request.form.get("Digits", "").strip()
    speech = (request.form.get("SpeechResult") or "").lower()

    # Route by keypad OR simple keyword rules
    if digit == "1" or "schedule" in speech or "book" in speech:
        return twiml("""<?xml version="1.0" encoding="UTF-8"?>
<Response><Redirect>/schedule</Redirect></Response>
""")

    if digit == "2" or "reschedule" in speech or "cancel" in speech:
        return twiml("""<?xml version="1.0" encoding="UTF-8"?>
<Response><Redirect>/reschedule</Redirect></Response>
""")

    if digit == "3" or "quote" in speech or "price" in speech or "cost" in speech:
        return twiml("""<?xml version="1.0" encoding="UTF-8"?>
<Response><Redirect>/quote</Redirect></Response>
""")

    # Fallback: loop back to the main menu
    return twiml("""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say>I’m sorry, I didn’t quite catch that. Let’s try again.</Say>
  <Redirect>/incoming-call</Redirect>
</Response>
""")

# ---------------------------
# Stub routes (B flows start here)
# ---------------------------

@app.route("/schedule", methods=["GET", "POST"])
def schedule():
    return Response("""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Gather input="speech"
          timeout="6"
          action="/schedule-name"
          method="POST">
    <Say>
      Great. Let’s get your call back scheduled.
      First, please tell me your name.
    </Say>
  </Gather>

  <Say>Sorry, I didn’t catch that.</Say>
  <Redirect>/schedule</Redirect>
</Response>
""", mimetype="text/xml")

    return Response(f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say>Thanks, {name}.</Say>
  <Gather input="speech"
          timeout="6"
          action="/schedule-time"
          method="POST">
    <Say>
      What day and time works best for your call back?
      For example, you can say tomorrow afternoon or Monday at 10 AM.
    </Say>
  </Gather>
  <Say>Sorry, I didn’t catch that.</Say>
  <Redirect>/schedule-name</Redirect>
</Response>
""", mimetype="text/xml")

@app.route("/schedule-time", methods=["POST"])
def schedule_time():
    time_pref = (request.form.get("SpeechResult") or "").strip()

    if not time_pref:
        return Response("""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say>Sorry, I didn’t catch the time.</Say>
  <Redirect>/schedule-name</Redirect>
</Response>
""", mimetype="text/xml")

    return Response(f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say>Great. I have you down for {time_pref}.</Say>
  <Say>We’ll call you back then.</Say>
  <Say>Thank you for calling OnCall Agency.</Say>
</Response>
""", mimetype="text/xml")

@app.route("/schedule-reason", methods=["POST"])
def schedule_reason():
    reason = request.form.get("SpeechResult", "")

    return Response("""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Gather input="dtmf"
          timeout="5"
          numDigits="1"
          action="/schedule-time"
          method="POST">
    <Say>
      Thanks. When would you like us to call you back?
      Press 1 for later today.
      Press 2 for tomorrow.
      Press 3 for another time.
    </Say>
  </Gather>

  <Say>Sorry, I didn’t catch that.</Say>
  <Redirect>/schedule</Redirect>
</Response>
""", mimetype="text/xml")

@app.route("/schedule-time", methods=["POST"])
def schedule_time():
    choice = request.form.get("Digits", "")

    return Response("""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say>
    Perfect. We’ll call you back during that time.
    We may send a confirmation text message.
    Standard messaging rates may apply.
    Do we have your permission to send that text?
  </Say>

  <Gather input="dtmf"
          timeout="5"
          numDigits="1"
          action="/schedule-confirm"
          method="POST">
    <Say>
      Press 1 to confirm.
      Press 2 to decline.
    </Say>
  </Gather>
</Response>
""", mimetype="text/xml")

@app.route("/schedule-confirm", methods=["POST"])
def schedule_confirm():
    consent = request.form.get("Digits", "")

    if consent == "1":
        return Response("""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say>
    You’re all set. We look forward to speaking with you.
    Goodbye.
  </Say>
</Response>
""", mimetype="text/xml")

    return Response("""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say>
    No problem. We’ll call you back without sending a text.
    Goodbye.
  </Say>
</Response>
""", mimetype="text/xml")

@app.route("/reschedule", methods=["GET", "POST"])
def reschedule():
    return twiml_say([
        "No problem. Let’s reschedule or cancel your appointment.",
        "In a moment, I’ll ask for your name and the appointment details."
    ])

@app.route("/quote", methods=["GET", "POST"])
def quote():
    return twiml_say([
        "Perfect. Let’s get you set up for a quote call back.",
        "In a moment, I’ll ask what you need and where the job is located."
    ])

# ---------------------------
# Run (Replit-safe port)
# ---------------------------

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "3000"))
    app.run(host="0.0.0.0", port=port, debug=True)

