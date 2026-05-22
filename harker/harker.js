// Load environment variables from .env file
const path = require('path')
const fs = require('fs')
const crypto = require('crypto')
require('dotenv').config({ path: path.join('/home/renfield/discord', '.env') })
require('uuid')
const oauthSignature = require('oauth-signature');
const express = require('express')
const helper = express()
const port = process.env.PORT || 1435

// Validate required environment variables
if (!process.env.DATABASE_USERNAME || !process.env.DATABASE_PASSWORD) {
  logError('Missing required environment variables: DATABASE_USERNAME or DATABASE_PASSWORD')
  process.exit(1)
}

// Logger setup
const logFile = '/home/renfield/logs/harker.log'
const logDir = '/home/renfield/logs'

// Ensure log directory exists
if (!fs.existsSync(logDir)) {
  fs.mkdirSync(logDir, { recursive: true })
}

function log(...args) {
  const timestamp = new Date().toISOString()
  const message = args.map(arg => typeof arg === 'object' ? JSON.stringify(arg) : arg).join(' ')
  const logMessage = `[${timestamp}] ${message}`
  console.log(logMessage)
  fs.appendFileSync(logFile, logMessage + '\n')
}

function logError(...args) {
  const timestamp = new Date().toISOString()
  const message = args.map(arg => typeof arg === 'object' ? JSON.stringify(arg) : arg).join(' ')
  const logMessage = `[${timestamp}] ERROR: ${message}`
  console.error(logMessage)
  fs.appendFileSync(logFile, logMessage + '\n')
}

// Database configuration from environment variables
const dbConfig = {
  host: 'localhost',
  user: process.env.DATABASE_USERNAME,
  password: process.env.DATABASE_PASSWORD,
  database: 'discordbot'
}

let pool;

// Rate limiting and state tracking
const requestCache = new Map(); // Track requests by IP
const stateTokens = new Map(); // Track valid state tokens
const RATE_LIMIT_WINDOW = 60000; // 1 minute
const RATE_LIMIT_MAX = 10; // 10 requests per window
const STATE_EXPIRY = 300000; // 5 minutes
const FETCH_TIMEOUT = 5000; // 5 seconds

function isRateLimited(ip) {
  const now = Date.now()
  if (!requestCache.has(ip)) {
    requestCache.set(ip, [])
  }
  const requests = requestCache.get(ip).filter(t => now - t < RATE_LIMIT_WINDOW)
  requestCache.set(ip, requests)
  if (requests.length >= RATE_LIMIT_MAX) return true
  requests.push(now)
  requestCache.set(ip, requests)
  return false
}

function generateStateToken() {
  const token = crypto.randomBytes(32).toString('hex')
  stateTokens.set(token, Date.now())
  return token
}

function validateStateToken(token) {
  if (!stateTokens.has(token)) return false
  const createdAt = stateTokens.get(token)
  if (Date.now() - createdAt > STATE_EXPIRY) {
    stateTokens.delete(token)
    return false
  }
  stateTokens.delete(token)
  return true
}

// Initialize MariaDB pool using dynamic import
(async () => {
  const mariadb = await import('mariadb');
  pool = mariadb.createPool(dbConfig);
})()


helper.get('/', (req, res) => {
  log('Received request at /')
  res.send('Harker is online!')
})

helper.listen(port, () => {
  log(`Harker is listening on port ${port}`)
})

helper.get('/auth-callback/', async (req, res) => {
  const clientIp = req.ip
  
  // Check rate limiting
  if (isRateLimited(clientIp)) {
    log('Rate limit exceeded for IP:', clientIp)
    return res.status(429).send('Too many requests')
  }

  log('Received auth callback')

  const { oauth_token, oauth_verifier, state } = req.query
  
  // Input validation
  if (!oauth_token || typeof oauth_token !== 'string' || oauth_token.length === 0) {
    log('Invalid oauth_token provided')
    return res.status(400).send('Invalid request')
  }
  if (!oauth_verifier || typeof oauth_verifier !== 'string' || oauth_verifier.length === 0) {
    log('Invalid oauth_verifier provided')
    return res.status(400).send('Invalid request')
  }
  // Validate state if present (optional for backward compatibility)
  if (state && !validateStateToken(state)) {
    log('Invalid or expired state token')
    return res.status(400).send('Invalid state token')
  }
  
  let wordpressUsername = ''
  let userId, server, oauth_nonce, oauth_timestamp, wordpress_users_api_route_result, urlwithParams

  // select * from wp_link where token = 'oauth_token'
  // if token exists, update the record with the new oauth_verifier
  // else, fail the authentication
  let conn;
  try {
    conn = await pool.getConnection();

    // --------------------------------------------------------
    // GET SECRET FOR THE USER WITH THE MATCHING OAUTH TOKEN
    // --------------------------------------------------------

    const rows = await conn.query("SELECT id, secret, server FROM wp_link WHERE token = ?", [oauth_token]);

    // check that one 1 record is returned
    if (rows.length === 0) {
      log('Token lookup failed')
      return res.status(400).send('Invalid token')
    } else if (rows.length > 1) {
      logError('Database integrity error: multiple token records')
      return res.status(500).send('Server error')
    }

    userId = rows[0].id
    const requestTokenSecret = rows[0].secret
    server = rows[0].server
    log('Token lookup successful')

    // do the next access query to get the new access token and secret using the oauth_verifier
    // if successful, update the database record with the new access token and secret, and set auth_status to "linked"
    // https://requests-oauthlib.readthedocs.io/en/latest/oauth1_workflow.html
    // renfield needs to check the auth status before doing any API calls to WordPress
    // --------------------------------------------------------
    // GET ACCESS URL
    // --------------------------------------------------------

    const accessUrlRow = await conn.query("SELECT setting_value FROM serversettings WHERE server = ? AND setting_name = 'oauth_access_url'", [server])
    if (accessUrlRow.length === 0 || accessUrlRow.length > 1) {
      logError('Server settings error for access URL')
      return res.status(500).send('Server error')
    }
    if (!accessUrlRow[0].setting_value) {
      logError('Access URL setting is empty')
      return res.status(500).send('Server error')
    }
    const accessUrl = accessUrlRow[0].setting_value
    log('Configuration retrieved')

    // --------------------------------------------------------
    // Get the consumer key and secret from the bot settings
    // --------------------------------------------------------
    const consumerKeyRow = await conn.query("SELECT setting_value FROM serversettings WHERE server = ? AND setting_name = 'consumer_key'", [server])
    const consumerSecretRow = await conn.query("SELECT setting_value FROM serversettings WHERE server = ? AND setting_name = 'consumer_secret'", [server])
    if (consumerKeyRow.length === 0 || consumerSecretRow.length === 0) {
      logError('Missing OAuth credentials')
      return res.status(500).send('Server error')
    }
    const consumerKey = consumerKeyRow[0].setting_value
    const consumerSecret = consumerSecretRow[0].setting_value
    log('OAuth credentials loaded')

    // --------------------------------------------------------
    // GET THE REAL ACCESS TOKEN AND SECRET USING THE OAUTH VERIFIER
    // --------------------------------------------------------
    // exchange the request token for an access token using the oauth_verifier
    oauth_nonce = require('uuid').v4()
    oauth_timestamp = Math.floor(Date.now() / 1000)

    var httpMethod = 'POST',
    url = accessUrl,
    parameters = {
        oauth_consumer_key : consumerKey,
        oauth_token : oauth_token,
        oauth_nonce : oauth_nonce,
        oauth_timestamp : oauth_timestamp,
        oauth_signature_method : 'HMAC-SHA1',
        oauth_version : '1.0',
        oauth_verifier : oauth_verifier
    },
    tokenSecret = requestTokenSecret,
    // generates a RFC 3986 encoded, BASE64 encoded HMAC-SHA1 hash
    encodedSignature = oauthSignature.generate(httpMethod, url, parameters, consumerSecret, tokenSecret),
    // generates a BASE64 encode HMAC-SHA1 hash
    signature = oauthSignature.generate(httpMethod, url, parameters, consumerSecret, tokenSecret,
        { encodeSignature: false});

    log('OAuth signature generated')
    // make the request to exchange the request token for an access token
    const wpapiParams = new URLSearchParams();
    wpapiParams.append('oauth_consumer_key', consumerKey);
    wpapiParams.append('oauth_token', oauth_token);
    wpapiParams.append('oauth_nonce', oauth_nonce);
    wpapiParams.append('oauth_timestamp', oauth_timestamp);
    wpapiParams.append('oauth_signature_method', 'HMAC-SHA1');
    wpapiParams.append('oauth_version', '1.0');
    wpapiParams.append('oauth_verifier', oauth_verifier);
    wpapiParams.append('oauth_signature', encodedSignature);

    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), FETCH_TIMEOUT)
    let response
    try {
      response = await fetch(accessUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: wpapiParams,
        signal: controller.signal
      })
    } catch (err) {
      logError('Access token request failed: ' + (err.name === 'AbortError' ? 'timeout' : err.message))
      return res.status(500).send('Server error')
    } finally {
      clearTimeout(timeout)
    }

    const responseText = await response.text()
    log('Token exchange completed')
    console.log(responseText)

    // parse the response to get the new access token and secret
    const responseParams = new URLSearchParams(responseText);
    const accessToken = responseParams.get('oauth_token');
    const accessTokenSecret = responseParams.get('oauth_token_secret');

    if (!accessToken || !accessTokenSecret) {
      logError('Access token exchange failed')
      return res.status(500).send('Server error')
    }

    log('Access token obtained')

    // --------------------------------------------------------
    // SAVE THE NEW TOKENS
    // --------------------------------------------------------
    // update the record with the new access token and secret, and set auth_status to "linked"
    const result = await conn.query("UPDATE wp_link SET token = ?, secret = ?, auth_status = ? WHERE id = ?", [accessToken, accessTokenSecret, "linked", userId])

    if (result.affectedRows !== 1) {
      logError('Token update failed or affected wrong number of rows')
      return res.status(500).send('Server error')
    }
    log('Tokens saved')

    // --------------------------------------------------------
    // GET THE URL FOR THE WORDPRESS USERS API FROM THE DATABASE
    // --------------------------------------------------------    
    wordpress_users_api_route_result = await conn.query("SELECT setting_value FROM serversettings WHERE server = ? AND setting_name = 'wordpress_users_api_route'", [server])
    if (wordpress_users_api_route_result.length !== 1 || !wordpress_users_api_route_result[0].setting_value) {
      logError('WordPress API route configuration error')
      return res.status(500).send('Server error')
    }
    const wordpress_users_api_route = wordpress_users_api_route_result[0].setting_value
    log('API configuration loaded')

    // --------------------------------------------------------
    // GET THE WORDPRESS USERNAME USING THE ACCESS TOKEN
    // --------------------------------------------------------
    oauth_nonce = require('uuid').v4(); // generate a unique nonce using uuid
    oauth_timestamp = Math.floor(Date.now() / 1000); // current timestamp in seconds

    var httpMethod = 'GET',
    url = wordpress_users_api_route,

    parameters = {
        oauth_consumer_key : consumerKey,
        oauth_token : accessToken,
        oauth_nonce : oauth_nonce,
        oauth_timestamp : oauth_timestamp,
        oauth_signature_method : 'HMAC-SHA1',
        oauth_version : '1.0',
        context: 'edit'
    },
    tokenSecret = accessTokenSecret,
    encodedSignature = oauthSignature.generate(httpMethod, url, parameters, consumerSecret, tokenSecret),
    signature = oauthSignature.generate(httpMethod, url, parameters, consumerSecret, tokenSecret,
        { encodeSignature: false});
    
    log('Fetching user info')
    
    const apiParams = new URLSearchParams();
    apiParams.append('oauth_consumer_key', consumerKey);
    apiParams.append('oauth_token', accessToken);
    apiParams.append('oauth_nonce', oauth_nonce);
    apiParams.append('oauth_timestamp', oauth_timestamp);
    apiParams.append('oauth_signature_method', 'HMAC-SHA1');
    apiParams.append('oauth_version', '1.0');
    apiParams.append('oauth_signature', encodedSignature);

    urlwithParams = `${url}?${apiParams.toString()}&context=edit`
    
    const controller2 = new AbortController()
    const timeout2 = setTimeout(() => controller2.abort(), FETCH_TIMEOUT)
    let apiResponse
    try {
      apiResponse = await fetch(urlwithParams, {
        method: 'GET',
        signal: controller2.signal
      })
    } catch (err) {
      logError('User info request failed: ' + (err.name === 'AbortError' ? 'timeout' : err.message))
      return res.status(500).send('Server error')
    } finally {
      clearTimeout(timeout2)
    }

    let apiResponseJson
    try {
      apiResponseJson = await apiResponse.json()
    } catch (err) {
      logError('Failed to parse user info response')
      return res.status(500).send('Server error')
    }
    
    if (apiResponseJson.code) {
      logError('WordPress API returned an error')
      return res.status(500).send('Server error')
    }

    wordpressUsername = apiResponseJson.username

    if (!wordpressUsername || typeof wordpressUsername !== 'string') {
      logError('Invalid username in response')
      return res.status(500).send('Server error')
    }
    log('User info retrieved')

    const updateUsernameResult = await conn.query("UPDATE wp_link SET wordpress_id = ? WHERE id = ?", [wordpressUsername, userId])

    if (updateUsernameResult.affectedRows !== 1) {
      logError('Username update failed')
      return res.status(500).send('Server error')
    }
    log('User information saved')

    // Get the webhook URL for the server
    const webhookUrlResult = await conn.query("SELECT setting_value FROM serversettings WHERE server = ? AND setting_name = 'harker-webhook'", [server])
    if (webhookUrlResult.length !== 1 || !webhookUrlResult[0].setting_value) {
      logError('Webhook configuration error')
      return res.status(500).send('Server error')
    }
    const webhookUrl = webhookUrlResult[0].setting_value
    log('Webhook configured')

    // Send a message to the webhook URL to notify that the authentication was successful
    // Authentication successful
    // Wordress username: {wordpressUsername}
    // Database ID: {userId}

    const webhookPayload = {
      content: `Authentication successful
      Wordpress username: ${wordpressUsername}
      Database ID: ${userId}`
    };

    const controller3 = new AbortController()
    const timeout3 = setTimeout(() => controller3.abort(), FETCH_TIMEOUT)
    try {
      const webhookResponse = await fetch(webhookUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(webhookPayload),
        signal: controller3.signal
      })
      if (webhookResponse.ok) {
        log('Notification sent')
      } else {
        logError('Webhook response: ' + webhookResponse.status)
      }
    } catch (err) {
      logError('Webhook failed: ' + (err.name === 'AbortError' ? 'timeout' : err.message))
    } finally {
      clearTimeout(timeout3)
    }

    log('Authentication completed')

  } catch (err) {
    logError('Request error: ' + err.message);
    return res.status(500).send('Server error');
  } finally {
    if (conn) conn.release();
  }

  res.send(`
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Authentication Successful</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #8B0000 0%, #000000 100%);
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            color: #333;
        }
        .container {
            background: white;
            border-radius: 12px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
            padding: 40px;
            text-align: center;
            max-width: 400px;
            width: 90%;
        }
        .success-icon {
            width: 80px;
            height: 80px;
            margin-bottom: 20px;
            border-radius: 8px;
        }
        h1 {
            color: #DC143C;
            margin-bottom: 10px;
            font-size: 24px;
        }
        .username {
            background: #F0B8C0;
            padding: 10px 20px;
            border-radius: 6px;
            margin: 20px 0;
            font-weight: bold;
            color: #495057;
        }
        .message {
            color: #6c757d;
            margin-bottom: 30px;
            line-height: 1.5;
        }
    </style>
</head>
<body>
    <div class="container">
        <img class="success-icon" src="images/harker.png" alt="Harker">
        <h1>Authentication Successful!</h1>
        <div class="username">${wordpressUsername}</div>
        <p class="message">Your Discord account has been successfully linked to your WordPress account. You can now close this window and return to Discord.</p>
    </div>
</body>
</html>
  `)
})

