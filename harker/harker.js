// Load environment variables from .env file
const path = require('path')
require('dotenv').config({ path: path.join('/home/renfield/discord', '.env') })
require('uuid')
const oauthSignature = require('oauth-signature');
const express = require('express')
const helper = express()
const port = process.env.PORT || 1435

// Database configuration from environment variables
const dbConfig = {
  host: 'localhost',
  user: process.env.DATABASE_USERNAME,
  password: process.env.DATABASE_PASSWORD,
  database: 'discordbot'
}

let pool;

// Initialize MariaDB pool using dynamic import
(async () => {
  const mariadb = await import('mariadb');
  pool = mariadb.createPool(dbConfig);
})()


helper.get('/', (req, res) => {
  console.log('Received request at /')
  res.send('Harker is online!')
})

helper.listen(port, () => {
  console.log(`Harker is listening on port ${port}`)
})

helper.get('/auth-callback/', async (req, res) => {
  console.log('Received auth callback with query:', req.query)

  const { oauth_token, oauth_verifier, wp_scope } = req.query
  console.log('OAuth Token:', oauth_token)
  console.log('OAuth Verifier:', oauth_verifier)
  console.log('WP Scope:', wp_scope)
  let wordpressUsername = '';   // ← outer scope

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
      console.log('No matching token found in database')
      return res.status(400).send('Invalid token')
    } else if (rows.length > 1) {
      console.log('Multiple matching tokens found in database')
      return res.status(500).send('Database error: multiple records found')
    }

    userId = rows[0].id
    const requestTokenSecret = rows[0].secret
    server = rows[0].server
    console.log('Matching token found for user ID:', userId, ' on server:', server)

    // do the next access query to get the new access token and secret using the oauth_verifier
    // if successful, update the database record with the new access token and secret, and set auth_status to "linked"
    // https://requests-oauthlib.readthedocs.io/en/latest/oauth1_workflow.html
    // renfield needs to check the auth status before doing any API calls to WordPress
    // --------------------------------------------------------
    // GET ACCESS URL
    // --------------------------------------------------------

    const accessUrlRow = await conn.query("SELECT setting_value FROM serversettings WHERE server = ? AND setting_name = 'oauth_access_url'", [server])
    if (accessUrlRow.length === 0) {
      console.log('No access URL found in database for server:', server)
      return res.status(500).send('Database error: no access URL found for server')
    } else if (accessUrlRow.length > 1) {
      console.log('Multiple access URLs found in database for server:', server)
      return res.status(500).send('Database error: multiple access URLs found for server')
    }
    if (!accessUrlRow[0].setting_value) {
      console.log('Access URL is empty in database for server:', server)
      return res.status(500).send('Database error: access URL is empty for server')
    }
    if (accessUrlRow[0].setting_value === undefined) {
      console.log('Access URL is undefined in database for server:', server)
      return res.status(500).send('Database error: access URL is undefined for server')
    }
    const accessUrl = accessUrlRow[0].setting_value
    console.log('Access URL retrieved from database:', accessUrl)

    // --------------------------------------------------------
    // Get the consumer key and secret from the bot settings
    // --------------------------------------------------------
    const consumerKeyRow = await conn.query("SELECT setting_value FROM serversettings WHERE setting_name = 'consumer_key'")
    const consumerSecretRow = await conn.query("SELECT setting_value FROM serversettings WHERE setting_name = 'consumer_secret'")
    if (consumerKeyRow.length === 0 || consumerSecretRow.length === 0) {
      console.log('Consumer key or secret not found in database')
      return res.status(500).send('Database error: consumer key or secret not found')
    }
    const consumerKey = consumerKeyRow[0].setting_value
    const consumerSecret = consumerSecretRow[0].setting_value
    console.log('Consumer key and secret retrieved from database')

    // --------------------------------------------------------
    // GET THE REAL ACCESS TOKEN AND SECRET USING THE OAUTH VERIFIER
    // --------------------------------------------------------
    // exchange the request token for an access token using the oauth_verifier
    oauth_nonce = require('uuid').v4(); // generate a unique nonce using uuid
    oauth_timestamp = Math.floor(Date.now() / 1000); // current timestamp in seconds

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

    console.log('OAuth signature generated for access token request')
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

    const response = await fetch(accessUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: wpapiParams
    });

    const responseText = await response.text();
    console.log('Response from access token request:', responseText)

    // parse the response to get the new access token and secret
    const responseParams = new URLSearchParams(responseText);
    const accessToken = responseParams.get('oauth_token');
    const accessTokenSecret = responseParams.get('oauth_token_secret');

    if (!accessToken || !accessTokenSecret) {
      console.log('Access token or secret not found in response')
      return res.status(500).send('Authentication error: access token or secret not found in response')
    }

    console.log('Access token and secret obtained from access token request')

    // --------------------------------------------------------
    // SAVE THE NEW TOKENS
    // --------------------------------------------------------
    // update the record with the new access token and secret, and set auth_status to "linked"
    const result = await conn.query("UPDATE wp_link SET token = ?, secret = ?, auth_status = ? WHERE id = ?", [accessToken, accessTokenSecret, "linked", userId])
    console.log('Database update result:', result)

    if (result.affectedRows === 0) {
      console.log('No records updated in database')
      return res.status(500).send('Database error: failed to update authentication status')
    }
    if (result.affectedRows > 1) {
      console.log('Multiple records updated in database')
      return res.status(500).send('Database error: multiple records updated')
    }

    // --------------------------------------------------------
    // GET THE URL FOR THE WORDPRESS USERS API FROM THE DATABASE
    // --------------------------------------------------------    
    wordpress_users_api_route_result = await conn.query("SELECT setting_value FROM serversettings WHERE server = ? AND setting_name = 'wordpress_users_api_route'", [server])
    if (wordpress_users_api_route_result.length === 0) {
      console.log('No Wordpress users API route found in database for server:', server)
      return res.status(500).send('Database error: no Wordpress users API route found for server')
    }
    wordpress_users_api_route = wordpress_users_api_route_result[0].setting_value
    if (!wordpress_users_api_route) {
      console.log('Wordpress users API route is empty in database for server:', server)
      return res.status(500).send('Database error: Wordpress users API route is empty for server')
    }
    if (wordpress_users_api_route === undefined) {
      console.log('Wordpress users API route is undefined in database for server:', server)
      return res.status(500).send('Database error: Wordpress users API route is undefined for server')
    }
    console.log('Wordpress users API route retrieved from database:', wordpress_users_api_route)

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
    
    console.log('OAuth signature generated for worpress API request to get user info')
    
   // make the request to get the user info from the Wordpress API using the access token
    const apiParams = new URLSearchParams();
    apiParams.append('oauth_consumer_key', consumerKey);
    apiParams.append('oauth_token', accessToken);
    apiParams.append('oauth_nonce', oauth_nonce);
    apiParams.append('oauth_timestamp', oauth_timestamp);
    apiParams.append('oauth_signature_method', 'HMAC-SHA1');
    apiParams.append('oauth_version', '1.0');
    apiParams.append('oauth_signature', encodedSignature);

    urlwithParams = `${url}?${apiParams.toString()}&context=edit`
    console.log('Making API request to get user info with URL:', urlwithParams)
    const apiResponse = await fetch(urlwithParams, {
      method: 'GET'
    });

    const apiResponseJson = await apiResponse.json();
    console.log('Response from API request to get user info:', apiResponseJson)
    
    if (apiResponseJson.code) {
      console.log('Error from Wordpress API:', apiResponseJson.message)
      return res.status(500).send('Error from Wordpress API: ' + apiResponseJson.message)
    }

    wordpressUsername = apiResponseJson.username;


    if (!wordpressUsername) {
      console.log('Wordpress username not found in response')
      return res.status(500).send('Error from Wordpress API: username not found in response')
    }
    console.log('Wordpress username obtained from API response:', wordpressUsername)

    const updateUsernameResult = await conn.query("UPDATE wp_link SET wordpress_id = ? WHERE id = ?", [wordpressUsername, userId])
    console.log('Database update result for Wordpress username:', updateUsernameResult)

    if (updateUsernameResult.affectedRows === 0) {
      console.log('No records updated in database for Wordpress username')
      return res.status(500).send('Database error: failed to update Wordpress username')
    }
    if (updateUsernameResult.affectedRows > 1) {
      console.log('Multiple records updated in database for Wordpress username')
      return res.status(500).send('Database error: multiple records updated for Wordpress username')
    }

    // Get the webhook URL for the server
    const webhookUrlResult = await conn.query("SELECT setting_value FROM serversettings WHERE server = ? AND setting_name = 'harker-webhook'", [server])
    if (webhookUrlResult.length === 0) {
      console.log('No webhook URL found in database for server:', server)
      return res.status(500).send('Database error: no webhook URL found for server')
    }
    const webhookUrl = webhookUrlResult[0].setting_value
    if (!webhookUrl) {
      console.log('Webhook URL is empty in database for server:', server)
      return res.status(500).send('Database error: webhook URL is empty for server')
    }
    if (webhookUrl === undefined) {
      console.log('Webhook URL is undefined in database for server:', server)
      return res.status(500).send('Database error: webhook URL is undefined for server')
    }
    console.log('Webhook URL retrieved from database:', webhookUrl)

    // Send a message to the webhook URL to notify that the authentication was successful
    const webhookPayload = {
      content: `Authentication successful for user ${wordpressUsername} (ID: ${userId}) on server ${server}`
    };

    const webhookResponse = await fetch(webhookUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(webhookPayload)
    });

    if (!webhookResponse.ok) {
      console.log('Failed to send webhook notification:', webhookResponse.statusText)
    } else {
      console.log('Webhook notification sent successfully')
    }

    console.log('Authentication successful for user ID:', userId)

  } catch (err) {
    console.error('Database error:', err);
    return res.status(500).send('Database error occurred');
  } finally {
    if (conn) conn.release();
  }

  res.send('<p>Authentication successful for ' + wordpressUsername + '! You can close this window.</p>')
})

