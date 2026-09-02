// heliosbooth/js/i18n.js
//
// Minimal client-side i18n for the Helios voting booth (vote.html,
// single-ballot-verify.html) and its jTemplates fragments
// (heliosbooth/templates/*.html).
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
    // vote.html inline script
    leave_warning: "If you leave this page with an in-progress ballot, your ballot will be lost.",
    exit_confirm: "Are you sure you want to exit the booth and lose all information about your current ballot?",
    select_at_least: "You need to select at least {{min}} answer(s).",
    max_selected: "Maximum number of options selected.<br />To change your selection, please de-select a current selection first.",
    select_up_to: "You may select up to {{max}} choices total.",
    processing: "Processing...",
    encryption_problem: "there appears to be a problem with the encryption process.\nPlease email help@heliosvoting.org and indicate that your encryption process froze at {{percent}}%",
    audit_posted: "This audited ballot has been posted.\nRemember, this vote will only be used for auditing and will not be tallied.\nClick \"back to voting\" and cast a new ballot to make sure your vote counts.",
    ballot_tracker_for: "Your ballot tracker for {{name}}: {{hash}}",

    // templates/audit.html
    audit_title: "Your audited ballot",
    audit_important: "IMPORTANT",
    audit_important_desc: "this ballot, now that it has been audited, <em>will not be tallied</em>.",
    audit_cast_instructions: "To cast a ballot, you must click the \"Back to Voting\" button below, re-encrypt it, and choose \"cast\" instead of \"audit.\"",
    audit_why_label: "Why?",
    audit_why_text: "Helios prevents you from auditing and casting the same ballot to provide you with some protection against coercion.",
    audit_now_what_label: "Now what?",
    audit_select_link: "Select your ballot audit info",
    audit_copy_instructions: ", copy it to your clipboard, then use the",
    audit_verifier_link: "ballot verifier",
    audit_to_verify: "to verify it.",
    audit_once_satisfied: "Once you're satisfied, click the \"back to voting\" button to re-encrypt and cast your ballot.",
    audit_before_going_back: "Before going back to voting,",
    audit_post_explain: "you can post this audited ballot to the Helios tracking center so that others might double-check the verification of this ballot.",
    audit_even_if_posted: "Even if you post your audited ballot, you must go back to voting and choose \"cast\" if you want your vote to count.",
    audit_back_to_voting_btn: "back to voting",
    audit_post_button: "post audited ballot to tracking center",

    // templates/done.html
    done_title: "Your Vote is Being Submitted",
    done_wait: "Please wait a few seconds while your vote is submitted to the casting server....",

    // templates/election.html
    election_intro: "To vote, follow these steps:",
    election_step_select_label: "Select",
    election_step_select_text: "your preferred options.",
    election_step_review_label: "Review",
    election_step_review_text: "your choices, which are then encrypted.",
    election_step_submit_label: "Submit",
    election_step_submit_text: "your encrypted ballot and authenticate to verify your eligibility.",
    election_start_button: "Start",
    election_help_prefix: "You can",
    election_email_help: "email for help",

    // templates/question.html
    question_number_of: "of",
    question_vote_for: "vote for",
    question_to: "to",
    question_at_least: "at least",
    question_up_to: "up to",
    question_approve_any: "as many as you approve of",
    question_more_info: "more info",
    question_proceed: "Proceed",
    question_previous: "Previous",
    question_next: "Next",

    // templates/seal.html
    seal_title: "Review your Ballot",
    seal_question_label: "Question #",
    seal_no_choice: "No choice selected",
    seal_selections_out_of: "selections out of possible",
    seal_change: "change",
    seal_tracker_is: "Your ballot tracker is",
    seal_proceed_login: "Proceed to Login",
    seal_spoil_audit: "Spoil & Audit",
    seal_optional: "[optional]",
    seal_spoil_explain: "If you choose, you can spoil this ballot and reveal how your choices were encrypted. This is an optional auditing process.",
    seal_spoil_guide: "You will then be guided to re-encrypt your choices for final casting.",

    // templates/submit.html
    submit_title: "Submit Your Encrypted Ballot",
    submit_info_removed_1: "All information, other than your encrypted ballot,",
    submit_info_removed_2: "has been removed from memory.",
    submit_tracking_reminder: "As a reminder, your ballot tracking number is:",
    submit_will_submit_to: "According to the election definition file, this ballot will be submitted to:",
    submit_login_notice: "where you will log in to validate your eligibility to vote.",
    submit_submit_button: "Submit Ballot",

    // templates/footer.html
    footer_bogus_key: "The public key for this election is not yet ready. This election is in preview mode only.",
    footer_fingerprint: "Election Fingerprint:",

    // single-ballot-verify.html inline script
    verifier_loading_election: "loading election...",
    verifier_cast_ballot_error: "\n\nIt looks like you are trying to verify a cast ballot. That can't be done, only audited ballots can be verified.",
    verifier_success_verification: "SUCCESSFUL VERIFICATION, DONE!",
    verifier_verification_problem: "PROBLEM - THIS BALLOT DOES NOT VERIFY.",
    verifier_load_problem: "PROBLEM LOADING election. Are you sure you have the right election URL?<br />",

    // vote.html static page chrome (title, banner, progress steps,
    // loading/error panels) — applied via data-i18n
    page_title: "Helios Voting Booth",
    exit_link: "exit",
    progress_select: "Select",
    progress_review: "Review",
    progress_submit: "Submit",
    loading_election_booth: "Checking capabilities and loading election booth...",
    loading_seconds: "This may take up to 10 seconds",
    error_title: "There's a problem",
    error_js_missing: "It appears that your browser does not have Java enabled. Helios needs Java to perform encryption within the browser.",
    error_js_install: "You may be able to install Java by visiting <a target=\"_new\" href=\"http://java.com\">java.com</a>.",
    processing_title: "Processing....",
    encrypting_ballot: "Helios is now encrypting your ballot<br />",
    encrypting_up_to_two_minutes: "This may take up to two minutes.",

    // single-ballot-verify.html static page chrome
    single_verify_page_title: "Helios Voting System",
    single_verify_heading: "Helios Single-Ballot Verifier",
    single_verify_loading: "Loading verifier...",
    single_verify_no_java: "Your browser does not have the Java plugin installed.<br /><br />At this time, the Java plugin is required for browser-based ballot auditing, although it is not required for ballot preparation.",
    single_verify_intro: "This single-ballot verifier lets you enter an audited ballot<br />and verify that it was prepared correctly.",
    single_verify_enter_url: "Enter the Election URL:",
    single_verify_your_ballot: "Your Ballot:",
    single_verify_submit_button: "Verify"
  },

  es: {
    // vote.html inline script
    leave_warning: "Si abandona esta página con una papeleta en curso, su papeleta se perderá.",
    exit_confirm: "¿Está seguro de que desea salir de la cabina de votación y perder toda la información sobre su papeleta actual?",
    select_at_least: "Debe seleccionar al menos {{min}} respuesta(s).",
    max_selected: "Número máximo de opciones seleccionado.<br />Para cambiar su selección, primero anule una selección actual.",
    select_up_to: "Puede seleccionar hasta {{max}} opciones en total.",
    processing: "Procesando...",
    encryption_problem: "parece que hay un problema con el proceso de cifrado.\nPor favor, envíe un correo electrónico a help@heliosvoting.org e indique que su proceso de cifrado se detuvo en {{percent}}%",
    audit_posted: "Esta papeleta auditada ha sido publicada.\nRecuerde que este voto solo se utilizará para la auditoría y no será escrutado.\nHaga clic en \"volver a votar\" y emita una nueva papeleta para asegurarse de que su voto cuente.",
    ballot_tracker_for: "Su código de verificación para {{name}}: {{hash}}",

    // templates/audit.html
    audit_title: "Su papeleta auditada",
    audit_important: "IMPORTANTE",
    audit_important_desc: "esta papeleta, ahora que ha sido auditada, <em>no será escrutada</em>.",
    audit_cast_instructions: "Para emitir una papeleta, debe hacer clic en el botón \"Volver a votar\" que aparece a continuación, volver a cifrarla y elegir \"emitir\" en lugar de \"auditar\".",
    audit_why_label: "¿Por qué?",
    audit_why_text: "Helios le impide auditar y emitir la misma papeleta para ofrecerle cierta protección contra la coacción.",
    audit_now_what_label: "¿Y ahora qué?",
    audit_select_link: "Seleccione la información de auditoría de su papeleta",
    audit_copy_instructions: ", cópiela en el portapapeles y luego use el",
    audit_verifier_link: "verificador de papeletas",
    audit_to_verify: "para verificarla.",
    audit_once_satisfied: "Una vez que esté conforme, haga clic en el botón \"volver a votar\" para volver a cifrar y emitir su papeleta.",
    audit_before_going_back: "Antes de volver a votar,",
    audit_post_explain: "puede publicar esta papeleta auditada en el centro de seguimiento de Helios para que otras personas puedan verificar la auditoría de esta papeleta.",
    audit_even_if_posted: "Incluso si publica su papeleta auditada, debe volver a votar y elegir \"emitir\" si quiere que su voto cuente.",
    audit_back_to_voting_btn: "volver a votar",
    audit_post_button: "publicar papeleta auditada en el centro de seguimiento",

    // templates/done.html
    done_title: "Su voto se está enviando",
    done_wait: "Espere unos segundos mientras su voto se envía al servidor de emisión....",

    // templates/election.html
    election_intro: "Para votar, siga estos pasos:",
    election_step_select_label: "Seleccionar",
    election_step_select_text: "sus opciones preferidas.",
    election_step_review_label: "Revisar",
    election_step_review_text: "sus elecciones, que a continuación se cifran.",
    election_step_submit_label: "Enviar",
    election_step_submit_text: "su papeleta cifrada y autentíquese para verificar su elegibilidad.",
    election_start_button: "Comenzar",
    election_help_prefix: "Puede",
    election_email_help: "enviar un correo electrónico para solicitar ayuda",

    // templates/question.html
    question_number_of: "de",
    question_vote_for: "vote por",
    question_to: "a",
    question_at_least: "al menos",
    question_up_to: "hasta",
    question_approve_any: "tantas como apruebe",
    question_more_info: "más información",
    question_proceed: "Continuar",
    question_previous: "Anterior",
    question_next: "Siguiente",

    // templates/seal.html
    seal_title: "Revise su papeleta",
    seal_question_label: "Pregunta n.º",
    seal_no_choice: "Ninguna opción seleccionada",
    seal_selections_out_of: "selecciones posibles de",
    seal_change: "cambiar",
    seal_tracker_is: "Su código de verificación es",
    seal_proceed_login: "Continuar para iniciar sesión",
    seal_spoil_audit: "Anular y auditar",
    seal_optional: "[opcional]",
    seal_spoil_explain: "Si lo desea, puede anular esta papeleta y revelar cómo se cifraron sus elecciones. Este es un proceso de auditoría opcional.",
    seal_spoil_guide: "A continuación, se le guiará para volver a cifrar sus elecciones para la emisión final.",

    // templates/submit.html
    submit_title: "Envíe su papeleta cifrada",
    submit_info_removed_1: "Toda la información, excepto su papeleta cifrada,",
    submit_info_removed_2: "se ha eliminado de la memoria.",
    submit_tracking_reminder: "Como recordatorio, su código de verificación de la papeleta es:",
    submit_will_submit_to: "Según el archivo de definición de la elección, esta papeleta se enviará a:",
    submit_login_notice: "donde iniciará sesión para validar su elegibilidad para votar.",
    submit_submit_button: "Enviar papeleta",

    // templates/footer.html
    footer_bogus_key: "La clave pública de esta elección aún no está lista. Esta elección se encuentra solo en modo de vista previa.",
    footer_fingerprint: "Huella digital de la elección:",

    // single-ballot-verify.html inline script
    verifier_loading_election: "cargando la elección...",
    verifier_cast_ballot_error: "\n\nParece que está intentando verificar una papeleta ya emitida. Eso no es posible; solo se pueden verificar las papeletas auditadas.",
    verifier_success_verification: "VERIFICACIÓN EXITOSA, TERMINADO",
    verifier_verification_problem: "PROBLEMA: ESTA PAPELETA NO SE VERIFICA.",
    verifier_load_problem: "PROBLEMA AL CARGAR LA ELECCIÓN. ¿Está seguro de que tiene la URL de elección correcta?<br />",

    // vote.html static page chrome
    page_title: "Cabina de votación Helios",
    exit_link: "salir",
    progress_select: "Seleccionar",
    progress_review: "Revisar",
    progress_submit: "Enviar",
    loading_election_booth: "Comprobando capacidades y cargando la cabina de votación...",
    loading_seconds: "Esto puede tardar hasta 10 segundos",
    error_title: "Hay un problema",
    error_js_missing: "Parece que su navegador no tiene Java habilitado. Helios necesita Java para realizar el cifrado dentro del navegador.",
    error_js_install: "Es posible que pueda instalar Java visitando <a target=\"_new\" href=\"http://java.com\">java.com</a>.",
    processing_title: "Procesando....",
    encrypting_ballot: "Helios está cifrando su papeleta<br />",
    encrypting_up_to_two_minutes: "Esto puede tardar hasta dos minutos.",

    // single-ballot-verify.html static page chrome
    single_verify_page_title: "Sistema de votación Helios",
    single_verify_heading: "Verificador de papeleta única de Helios",
    single_verify_loading: "Cargando verificador...",
    single_verify_no_java: "Su navegador no tiene instalado el complemento de Java.<br /><br />Actualmente, el complemento de Java es necesario para la auditoría de papeletas en el navegador, aunque no es necesario para la preparación de la papeleta.",
    single_verify_intro: "Este verificador de papeleta única le permite introducir una papeleta auditada<br />y comprobar que se preparó correctamente.",
    single_verify_enter_url: "Introduzca la URL de la elección:",
    single_verify_your_ballot: "Su papeleta:",
    single_verify_submit_button: "Verificar"
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
