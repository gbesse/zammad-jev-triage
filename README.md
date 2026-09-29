# Zammad Jev Triage

Experimental community alpha v0.1.1 · MIT.

## Français

Un service reçoit les articles client Zammad, vérifie la signature HMAC, décide de l’équipe et met à jour `group_id` si une correspondance explicite est configurée. Les cas incertains restent à revoir.

Installation :

```sh
python3 app.py
```

Variables serveur : `TYPESAFE_API_KEY, ZAMMAD_WEBHOOK_SECRET, ZAMMAD_URL, ZAMMAD_API_TOKEN, ZAMMAD_GROUP_IDS (JSON; example: {"billing":2,"technical":3})`. Garder les secrets hors du dépôt et de la configuration visible par les utilisateurs.

Créer un webhook Zammad vers `/webhook` avec un secret HMAC SHA1 et un trigger sur les tickets entrants. Le service ignore les articles non clients et les affectations déjà correctes.

Les articles internes, même marqués comme provenant d’un client, sont ignorés. Les charges JSON invalides reçoivent une réponse 400.

## English

A service receives Zammad customer articles, verifies their HMAC signature, decides the team, and updates `group_id` when an explicit mapping is configured. Uncertain cases stay for review.

Setup:

```sh
python3 app.py
```

Server variables: `TYPESAFE_API_KEY, ZAMMAD_WEBHOOK_SECRET, ZAMMAD_URL, ZAMMAD_API_TOKEN, ZAMMAD_GROUP_IDS (JSON; example: {"billing":2,"technical":3})`. Keep secrets outside the repository and user-visible configuration.

Create a Zammad webhook to `/webhook` with an HMAC SHA1 secret and a trigger for incoming tickets. The service ignores non-customer articles and already-correct assignments.

Internal articles are ignored even when marked as customer articles. Invalid JSON payloads receive a 400 response.

## Español

Un servicio recibe artículos de clientes de Zammad, verifica la firma HMAC, decide el equipo y actualiza `group_id` cuando hay una asignación explícita. Los casos inciertos quedan para revisión.

Instalación:

```sh
python3 app.py
```

Variables del servidor: `TYPESAFE_API_KEY, ZAMMAD_WEBHOOK_SECRET, ZAMMAD_URL, ZAMMAD_API_TOKEN, ZAMMAD_GROUP_IDS (JSON; example: {"billing":2,"technical":3})`. Mantén los secretos fuera del repositorio y de la configuración visible para usuarios.

Crea un webhook de Zammad hacia `/webhook` con un secreto HMAC SHA1 y un trigger para tickets entrantes. El servicio omite artículos que no son de clientes y asignaciones ya correctas.

Se omiten los artículos internos aunque estén marcados como artículos de clientes. Las cargas JSON inválidas reciben una respuesta 400.

## Verification / Vérification / Verificación

```sh
python3 -m unittest discover -s tests -v
```

Tests use synthetic Jev responses and host event fixtures. Threshold `0.9` in `policy.json` is an example and must be calibrated on labeled data before automatic actions. No live host or Jev service has been exercised. / Les tests utilisent des réponses synthétiques et le seuil doit être calibré ; aucun hôte ni service Jev réel n’a été testé. / Las pruebas usan respuestas sintéticas y el umbral debe calibrarse; no se ha probado un host ni un servicio Jev real.

Host reference / Référence de l’hôte / Referencia del host: https://admin-docs.zammad.org/en/latest/manage/webhook/payload.html

The receiver listens on `127.0.0.1:8080` by default; use a TLS reverse proxy for remote webhooks. `LISTEN_HOST` and `PORT` can override the bind address. / Le service écoute par défaut sur `127.0.0.1:8080` ; utiliser un proxy TLS pour les webhooks distants. / El servicio escucha por defecto en `127.0.0.1:8080`; usa un proxy TLS para webhooks remotos.
