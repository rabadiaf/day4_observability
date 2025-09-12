
# Runbook – /health alert

1) **Alert received**: /health returned non-200.
2) **Check recent logs**: re-run `bash check_health.sh`; inspect JSON body & latency.
3) **Identify change**: was `STATUS_CODE` env var changed? any new deploys?
4) **Mitigate**: roll back to last good version or reset env var to 200.
5) **Verify**: re-run health check until 200 and latency within normal bounds.

3) Ejecutar (paso a paso)

cd day4_observability

# 1) Empaquetar y crear/actualizar Lambda (STATUS_CODE=200)
bash package_lambda.sh

# 2) Crear/configurar API y obtener URL
python3 api_setup.py    # copia la URL impresa

# 3) Probar salud (OK)
bash check_health.sh    # o: bash check_health.sh "<URL>"

Deberías ver OK con un JSON que incluye latency_ms.



4) Simular fallo y alerta

# Cambia STATUS_CODE a 500 en la configuración de la función
awsls --endpoint-url http://localhost:4566 lambda update-function-configuration \
  --function-name obs-health \
  --environment "Variables={STATUS_CODE=500}"

# Vuelve a probar
bash check_health.sh    # ahora debe decir ALERT (status=500)

# Recuperación
awsls --endpoint-url http://localhost:4566 lambda update-function-configuration \
  --function-name obs-health \
  --environment "Variables={STATUS_CODE=200}"
bash check_health.sh    # vuelve a OK


5) ¿Qué logras con el Día 4?

Endpoint de salud real con latencia y código de estado.

Check automatizado que marca OK/ALERT.

Runbook breve y accionable (alert → diagnóstico → mitigación → verificación → cierre).

Frase para el panel (10–15 s)

“Implementé un /health con latencia y un chequeo automático que alerta si falla; tengo un runbook de 5 pasos para responder rápido y verificar recuperación.”
