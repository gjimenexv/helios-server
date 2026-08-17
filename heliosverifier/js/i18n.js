// heliosverifier/js/i18n.js
//
// Minimal client-side i18n for the Helios ballot-audit verifier
// (heliosverifier/verify.html). This is a standalone duplicate of
// heliosbooth/js/i18n.js's API (BOOTH_I18N / BOOTH_LANG / T) rather than a
// shared include, because /booth/ and /verifier/ are two separate,
// non-nested Django static-serve roots (see urls.py), so a relative path
// from one into the other does not resolve to a valid URL.
//
// - BOOTH_I18N holds all user-visible strings, keyed by language code.
// - BOOTH_LANG is resolved once from the `lang` query-string parameter
//   (defaults to 'en' if absent or not one of the supported languages).
// - T(key, vars) looks up BOOTH_I18N[BOOTH_LANG][key], falling back to
//   English, then to the raw key. If `vars` is given (a plain object),
//   `{{varname}}` placeholders in the string are replaced with the
//   corresponding value from `vars`.

var BOOTH_I18N = {
  en: {
    verifier_no_java: "sorry, in-browser verification requires Java Support at this time.",
    verifier_election_header: "Election",
    verifier_loading_election: "loading election...",
    verifier_loaded_election: "loaded election: {{name}}",
    verifier_election_fingerprint: "election fingerprint: {{hash}}",
    verifier_not_homomorphic: "PROBLEM: this election is not a straight-forward homomorphic-tally election. As a result, Helios cannot currently verify it.",
    verifier_loading_voters: "loading list of voters...",
    verifier_loaded_voter_list: "loaded voter list, now loading ballots for each..",
    verifier_ballots_header: "Ballots",
    verifier_voter_num: "Voter #{{num}}",
    verifier_uuid_label: "-- UUID: {{uuid}}",
    verifier_tracking_number: "-- Ballot Tracking Number: {{hash}}",
    verifier_question_option: "Question #{{qnum}}, Option #{{onum}} -- {{result}}",
    verifier_question_overall: "Question #{{qnum}} OVERALL -- {{result}}",
    verifier_trustees_header: "Trustees",
    verifier_trustee_num: "Trustee #{{num}}: {{email}}",
    verifier_pk_verified: "-- PK {{hash}} -- VERIFIED.",
    verifier_pk_error: "==== ERROR for PK of trustee {{email}}",
    verifier_pubkey_correct: "election public key CORRECTLY FORMED",
    verifier_pubkey_error: "==== ERROR, election public key doesn't match",
    verifier_tally_header: "Tally",
    verifier_question_num_name: "Question #{{num}}: {{name}}",
    verifier_answer_count: "Answer #{{num}}: {{answer}} - COUNT = {{count}}",
    verifier_decryption_verifies: "-- Trustee {{email}}: decryption factor verifies",
    verifier_decryption_error: "==== ERROR with Trustee {{email}}: decryption factor does not verify",
    verifier_final_result_header: "FINAL RESULT",
    verifier_fully_verified: "ELECTION FULLY VERIFIED -- SUCCESS!",
    verifier_verification_failed: "VERIFICATION FAILED",
    verifier_private_election: "<p>It appears that you are trying to verify a private election.</p>",
    verifier_login_options: "<p>You can log in as a valid voter or log in as the election admin.</p>",
    verifier_login_as_voter: "Log in as a valid voter",
    verifier_login_as_admin: "Log in as the election admin",
    verifier_verified: "VERIFIED",
    verifier_fail: "FAIL",
    verifier_loading_ballot_num: "loading ballot for voter #{{num}}",
    verifier_no_ballot: "no ballot for this voter #{{num}}",
    verifier_found_ballot: "FOUND a ballot for voter #{{num}}",

    // verify.html static page chrome
    page_title: "Helios Voting System -- Verifier",
    banner_title: "Helios Election Verifier",
    loading_verifier: "loading verifier ...",
    enter_election_url: "Enter the Election URL:",
    start_verification_button: "start verification"
  },

  es: {
    verifier_no_java: "lo sentimos, la verificación en el navegador requiere compatibilidad con Java en este momento.",
    verifier_election_header: "Elección",
    verifier_loading_election: "cargando la elección...",
    verifier_loaded_election: "elección cargada: {{name}}",
    verifier_election_fingerprint: "huella digital de la elección: {{hash}}",
    verifier_not_homomorphic: "PROBLEMA: esta elección no es una elección de escrutinio homomórfico directo. Por lo tanto, Helios no puede verificarla actualmente.",
    verifier_loading_voters: "cargando la lista de votantes...",
    verifier_loaded_voter_list: "lista de votantes cargada, ahora cargando las papeletas de cada uno..",
    verifier_ballots_header: "Papeletas",
    verifier_voter_num: "Votante n.º {{num}}",
    verifier_uuid_label: "-- UUID: {{uuid}}",
    verifier_tracking_number: "-- Número de seguimiento de la papeleta: {{hash}}",
    verifier_question_option: "Pregunta n.º {{qnum}}, Opción n.º {{onum}} -- {{result}}",
    verifier_question_overall: "Pregunta n.º {{qnum}} EN GENERAL -- {{result}}",
    verifier_trustees_header: "Fiduciarios",
    verifier_trustee_num: "Fiduciario n.º {{num}}: {{email}}",
    verifier_pk_verified: "-- Clave pública {{hash}} -- VERIFICADA.",
    verifier_pk_error: "==== ERROR en la clave pública del fiduciario {{email}}",
    verifier_pubkey_correct: "la clave pública de la elección está CORRECTAMENTE FORMADA",
    verifier_pubkey_error: "==== ERROR, la clave pública de la elección no coincide",
    verifier_tally_header: "Escrutinio",
    verifier_question_num_name: "Pregunta n.º {{num}}: {{name}}",
    verifier_answer_count: "Respuesta n.º {{num}}: {{answer}} - RECUENTO = {{count}}",
    verifier_decryption_verifies: "-- Fiduciario {{email}}: el factor de descifrado se verifica",
    verifier_decryption_error: "==== ERROR con el fiduciario {{email}}: el factor de descifrado no se verifica",
    verifier_final_result_header: "RESULTADO FINAL",
    verifier_fully_verified: "ELECCIÓN COMPLETAMENTE VERIFICADA -- ¡ÉXITO!",
    verifier_verification_failed: "LA VERIFICACIÓN FALLÓ",
    verifier_private_election: "<p>Parece que está intentando verificar una elección privada.</p>",
    verifier_login_options: "<p>Puede iniciar sesión como votante válido o como administrador de la elección.</p>",
    verifier_login_as_voter: "Iniciar sesión como votante válido",
    verifier_login_as_admin: "Iniciar sesión como administrador de la elección",
    verifier_verified: "VERIFICADO",
    verifier_fail: "FALLO",
    verifier_loading_ballot_num: "cargando la papeleta del votante n.º {{num}}",
    verifier_no_ballot: "no hay papeleta para este votante n.º {{num}}",
    verifier_found_ballot: "SE ENCONTRÓ una papeleta para el votante n.º {{num}}",

    // verify.html static page chrome
    page_title: "Sistema de votación Helios -- Verificador",
    banner_title: "Verificador de elecciones Helios",
    loading_verifier: "cargando verificador...",
    enter_election_url: "Introduzca la URL de la elección:",
    start_verification_button: "iniciar verificación"
  }
};

// Resolve the active language once, from the `lang` query-string parameter.
// Falls back to 'en' if the parameter is absent or not a supported language.
// Uses the jquery.query plugin (already loaded before this file), which
// exposes $.query.get('paramname').
BOOTH_LANG = (function() {
  var supported = { en: true, es: true };
  var requested = null;
  try {
    if (window.jQuery && jQuery.query && typeof jQuery.query.get === 'function') {
      var val = jQuery.query.get('lang');
      if (val && val !== true) {
        requested = val;
      }
    }
  } catch (e) {
    // fall through to default
  }
  if (requested && supported[requested]) {
    return requested;
  }
  return 'en';
})();

// Look up a translation string by key, with optional {{varname}} substitution.
// `vars`, if provided, is a plain object whose keys are substituted in place
// of `{{key}}` placeholders in the translated string.
function T(key, vars) {
  var lang_table = BOOTH_I18N[BOOTH_LANG] || BOOTH_I18N.en;
  var str = lang_table[key];
  if (typeof str === 'undefined')
    str = BOOTH_I18N.en[key];
  if (typeof str === 'undefined')
    str = key;

  if (vars) {
    for (var varname in vars) {
      if (Object.prototype.hasOwnProperty.call(vars, varname)) {
        str = str.replace(new RegExp('\\{\\{' + varname + '\\}\\}', 'g'), vars[varname]);
      }
    }
  }

  return str;
}
