"""Selenium tests for impossible-ma.html.

Page-ready signal: window.PYODIDE_READY === true.
Cold Pyodide load ~170s — fixtures use module scope so we pay that once.
"""
import http.server
import json as _json
import os
import socketserver
import threading
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "impossible-ma.html"
PORT = 8765
PAGE_URL = f"http://localhost:{PORT}/impossible-ma.html"
# Cold Pyodide load observed 170s-300s depending on host network + WASM compile
# speed. Env override lets fast CI machines shorten the wait if needed.
PAGE_READY_TIMEOUT = int(os.environ.get("PAGE_READY_TIMEOUT", "450"))


@pytest.fixture(scope="module")
def server():
    handler = http.server.SimpleHTTPRequestHandler
    cwd_before = os.getcwd()
    os.chdir(ROOT)
    httpd = socketserver.TCPServer(("", PORT), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield
    finally:
        httpd.shutdown()
        httpd.server_close()
        os.chdir(cwd_before)


@pytest.fixture(scope="module")
def driver(server):
    if not HTML.exists():
        pytest.skip(f"{HTML} missing - run `python scripts/build_html.py` first")
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--window-size=1400,900")
    drv = webdriver.Chrome(options=opts)
    try:
        drv.get(PAGE_URL)
        WebDriverWait(drv, PAGE_READY_TIMEOUT).until(
            lambda d: d.execute_script(
                "return window.PYODIDE_READY === true || window.PYODIDE_LOAD_ERROR != null"
            )
        )
        err = drv.execute_script("return window.PYODIDE_LOAD_ERROR")
        if err:
            pytest.fail(f"Pyodide failed to load: {err}")
        yield drv
    finally:
        drv.quit()


@pytest.fixture
def page(driver):
    # Do NOT reload the page — the module-scoped driver fixture already loaded
    # Pyodide + the wheel once (~170s). Reloading would force another cold
    # Pyodide load and blow the per-test timeout. Instead, reset DOM/form
    # state in-place so tests are isolated without paying the load cost again.
    driver.execute_script("""
        location.hash = '#k1';
        sessionStorage.clear();
        document.querySelectorAll('input[type="text"], input[type="number"], input[type="password"]')
            .forEach(i => { i.value = ''; });
        document.querySelectorAll('select').forEach(s => { s.selectedIndex = 0; });
        document.querySelectorAll('#k1-adjacent tbody, #adv-studies tbody')
            .forEach(t => t.innerHTML = '');
        document.getElementById('k1-error').hidden = true;
        document.getElementById('ms-error').hidden = true;
        document.getElementById('adv-error').hidden = true;
        document.getElementById('k1-result').hidden = true;
        document.getElementById('ms-result').hidden = true;
        document.getElementById('adv-result').hidden = true;
        if (typeof k1AddRow === 'function') { for (let i = 0; i < 3; i++) k1AddRow(); }
        if (typeof advAddRow === 'function') { for (let i = 0; i < 3; i++) advAddRow(); }
        if (typeof k1ValidateRunButton === 'function') k1ValidateRunButton();
        if (typeof msValidateRun === 'function') msValidateRun();
        if (typeof advValidateRun === 'function') advValidateRun();
        window.K1_LAST_ENVELOPE = null;
        window.MS_LAST_ENVELOPE = null;
        window.ADV_LAST_ENVELOPE = null;
    """)
    return driver


def _text_content(driver, elem_id):
    return driver.execute_script(
        f"return document.getElementById('{elem_id}').textContent;"
    ) or ""


# ---------------------------------------------------------------------------
# Task 11 — Infra + page-ready signal
# ---------------------------------------------------------------------------

def test_pyodide_ready_signal(driver):
    assert driver.execute_script("return window.PYODIDE_READY") is True


# ---------------------------------------------------------------------------
# Task 12 — Tab routing
# ---------------------------------------------------------------------------

def test_default_tab_is_k1(page):
    active = page.find_element(By.CSS_SELECTOR, ".tab-pane.active")
    assert active.get_attribute("data-pane") == "k1"


def test_hash_change_swaps_pane(page):
    page.execute_script("location.hash = '#missing_se';")
    WebDriverWait(page, 5).until(
        lambda d: d.find_element(By.CSS_SELECTOR, ".tab-pane.active").get_attribute(
            "data-pane"
        )
        == "missing_se"
    )


def test_truthcert_key_persists_in_sessionstorage(page):
    inp = page.find_element(By.ID, "truthcert-key")
    inp.send_keys("a" * 64)
    # Input event should fire automatically; if not, trigger it
    page.execute_script(
        "document.getElementById('truthcert-key').dispatchEvent(new Event('input'));"
    )
    stored = page.execute_script("return sessionStorage.getItem('truthcert_key');")
    assert stored == "a" * 64


# ---------------------------------------------------------------------------
# Task 13 — k=1 tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("dataset", ["rare_hf", "novel_device", "single_arm_oncology"])
def test_k1_dataset_runs_and_renders(page, dataset):
    Select(page.find_element(By.ID, "k1-dataset")).select_by_value(dataset)
    page.find_element(By.ID, "k1-load").click()
    WebDriverWait(page, 5).until(
        lambda d: not d.find_element(By.ID, "k1-run").get_attribute("disabled")
    )
    page.find_element(By.ID, "k1-run").click()
    WebDriverWait(page, 60).until(
        lambda d: d.execute_script("return window.K1_LAST_ENVELOPE != null")
        or not d.find_element(By.ID, "k1-error").get_attribute("hidden")
    )
    env = page.execute_script("return window.K1_LAST_ENVELOPE")
    err_text = page.find_element(By.ID, "k1-error").text
    assert env is not None, (
        f"K1_LAST_ENVELOPE is None for {dataset!r}; error box: {err_text!r}"
    )
    assert env["case"] == "k1"


def test_k1_form_entry_run(page):
    page.find_element(By.ID, "k1-target-est").send_keys("-0.4")
    page.find_element(By.ID, "k1-target-se").send_keys("0.2")
    rows = page.find_elements(By.CSS_SELECTOR, "#k1-adjacent tbody tr")
    assert len(rows) >= 3
    vals = [(-0.3, 0.15), (-0.25, 0.12), (-0.4, 0.18)]
    for tr, (e, s) in zip(rows[:3], vals):
        tr.find_element(By.CSS_SELECTOR, ".k1-est").send_keys(str(e))
        tr.find_element(By.CSS_SELECTOR, ".k1-se").send_keys(str(s))
    # Fire input events to trigger validation
    page.execute_script("k1ValidateRunButton();")
    WebDriverWait(page, 5).until(
        lambda d: not d.find_element(By.ID, "k1-run").get_attribute("disabled")
    )
    page.find_element(By.ID, "k1-run").click()
    WebDriverWait(page, 60).until(
        lambda d: d.execute_script("return window.K1_LAST_ENVELOPE != null")
    )
    env = page.execute_script("return window.K1_LAST_ENVELOPE")
    assert env is not None
    assert env["case"] == "k1"


def test_k1_invalid_target_se_keeps_run_disabled(page):
    page.find_element(By.ID, "k1-target-est").send_keys("-0.4")
    page.find_element(By.ID, "k1-target-se").send_keys("0")
    rows = page.find_elements(By.CSS_SELECTOR, "#k1-adjacent tbody tr")
    for tr in rows[:3]:
        tr.find_element(By.CSS_SELECTOR, ".k1-est").send_keys("-0.3")
        tr.find_element(By.CSS_SELECTOR, ".k1-se").send_keys("0.15")
    # Explicitly re-validate because input events may race
    page.execute_script("k1ValidateRunButton();")
    disabled = page.find_element(By.ID, "k1-run").get_attribute("disabled")
    assert disabled == "true", "k1-run should be disabled when target SE=0"


# ---------------------------------------------------------------------------
# Task 14 — missing_se tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("dataset", ["figure_only", "p_only", "multi_consistent"])
def test_missing_se_dataset_runs(page, dataset):
    page.execute_script("location.hash = '#missing_se';")
    WebDriverWait(page, 5).until(
        lambda d: d.find_element(By.CSS_SELECTOR, ".tab-pane.active").get_attribute(
            "data-pane"
        )
        == "missing_se"
    )
    Select(page.find_element(By.ID, "ms-dataset")).select_by_value(dataset)
    page.find_element(By.ID, "ms-load").click()
    WebDriverWait(page, 5).until(
        lambda d: not d.find_element(By.ID, "ms-run").get_attribute("disabled")
    )
    page.find_element(By.ID, "ms-run").click()
    WebDriverWait(page, 45).until(
        lambda d: d.execute_script("return window.MS_LAST_ENVELOPE != null")
        or not d.find_element(By.ID, "ms-error").get_attribute("hidden")
    )
    env = page.execute_script("return window.MS_LAST_ENVELOPE")
    err_text = page.find_element(By.ID, "ms-error").text
    assert env is not None, (
        f"MS_LAST_ENVELOPE is None for {dataset!r}; error box: {err_text!r}"
    )
    assert env["case"] == "missing_se"


def test_missing_se_no_route_keeps_run_disabled(page):
    page.execute_script("location.hash = '#missing_se';")
    WebDriverWait(page, 5).until(
        lambda d: d.find_element(By.CSS_SELECTOR, ".tab-pane.active").get_attribute(
            "data-pane"
        )
        == "missing_se"
    )
    # Provide only an effect value — no CI, no p-value, no statistic
    page.find_element(By.ID, "ms-effect").send_keys("0.4")
    page.execute_script("msValidateRun();")
    disabled = page.find_element(By.ID, "ms-run").get_attribute("disabled")
    assert disabled == "true", "ms-run should stay disabled when no SE route available"


# ---------------------------------------------------------------------------
# Task 15 — adversarial tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("dataset", ["pcsk9", "ace_legacy", "covid_early"])
def test_adversarial_dataset_runs(page, dataset):
    page.execute_script("location.hash = '#adversarial';")
    WebDriverWait(page, 5).until(
        lambda d: d.find_element(By.CSS_SELECTOR, ".tab-pane.active").get_attribute(
            "data-pane"
        )
        == "adversarial"
    )
    Select(page.find_element(By.ID, "adv-dataset")).select_by_value(dataset)
    page.find_element(By.ID, "adv-load").click()
    WebDriverWait(page, 5).until(
        lambda d: not d.find_element(By.ID, "adv-run").get_attribute("disabled")
    )
    page.find_element(By.ID, "adv-run").click()
    WebDriverWait(page, 120).until(
        lambda d: d.execute_script("return window.ADV_LAST_ENVELOPE != null")
        or not d.find_element(By.ID, "adv-error").get_attribute("hidden")
    )
    env = page.execute_script("return window.ADV_LAST_ENVELOPE")
    err_text = page.find_element(By.ID, "adv-error").text
    assert env is not None, (
        f"ADV_LAST_ENVELOPE is None for {dataset!r}; error box: {err_text!r}"
    )
    assert env["case"] == "adversarial"


def test_adversarial_csv_missing_column_shows_banner(page, tmp_path):
    # CSV with study/estimate/se but missing rob, n, followup, language, pub_type
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text(
        "study,estimate,se\nS1,0.1,0.2\nS2,-0.1,0.15\nS3,0.05,0.18\n",
        encoding="utf-8",
    )
    page.execute_script("location.hash = '#adversarial';")
    WebDriverWait(page, 5).until(
        lambda d: d.find_element(By.CSS_SELECTOR, ".tab-pane.active").get_attribute(
            "data-pane"
        )
        == "adversarial"
    )
    page.find_element(By.ID, "adv-csv").send_keys(str(bad_csv))
    WebDriverWait(page, 10).until(
        lambda d: not d.find_element(By.ID, "adv-error").get_attribute("hidden")
    )
    err = page.find_element(By.ID, "adv-error").text
    assert "missing columns" in err.lower() or "CSV missing" in err, (
        f"Expected 'missing columns' in error banner, got: {err!r}"
    )
    # Should mention at least one missing column name
    assert any(col in err for col in ("rob", "n", "followup", "language", "pub_type")), (
        f"Expected missing column names in banner, got: {err!r}"
    )


# ---------------------------------------------------------------------------
# Task 16 — TruthCert + report tests
# ---------------------------------------------------------------------------

def test_truthcert_export_without_key_alerts(page):
    # Load and run k=1 first
    Select(page.find_element(By.ID, "k1-dataset")).select_by_value("rare_hf")
    page.find_element(By.ID, "k1-load").click()
    WebDriverWait(page, 5).until(
        lambda d: not d.find_element(By.ID, "k1-run").get_attribute("disabled")
    )
    page.find_element(By.ID, "k1-run").click()
    WebDriverWait(page, 60).until(
        lambda d: d.execute_script("return window.K1_LAST_ENVELOPE != null")
    )
    # Intercept alert before clicking export
    page.execute_script(
        "window._lastAlert = null; window.alert = function(m) { window._lastAlert = m; };"
    )
    page.find_element(By.ID, "k1-export-json").click()
    WebDriverWait(page, 5).until(
        lambda d: d.execute_script("return window._lastAlert") is not None
    )
    msg = page.execute_script("return window._lastAlert")
    assert "TruthCert" in msg or "key" in msg.lower(), (
        f"Expected TruthCert/key mention in alert, got: {msg!r}"
    )


def test_truthcert_signed_bundle_round_trips(page):
    # Set key in footer
    key_inp = page.find_element(By.ID, "truthcert-key")
    key_inp.send_keys("a" * 64)
    page.execute_script(
        "document.getElementById('truthcert-key').dispatchEvent(new Event('input'));"
    )
    # Load and run
    Select(page.find_element(By.ID, "k1-dataset")).select_by_value("rare_hf")
    page.find_element(By.ID, "k1-load").click()
    WebDriverWait(page, 5).until(
        lambda d: not d.find_element(By.ID, "k1-run").get_attribute("disabled")
    )
    page.find_element(By.ID, "k1-run").click()
    WebDriverWait(page, 60).until(
        lambda d: d.execute_script("return window.K1_LAST_ENVELOPE != null")
    )
    # Sign and verify via Pyodide (runs in-browser Python)
    bundle_json = page.execute_async_script(r"""
const cb = arguments[arguments.length - 1];
(async () => {
  try {
    const env = window.K1_LAST_ENVELOPE;
    window.PYODIDE.globals.set('SP', window.PYODIDE.toPy(env));
    window.PYODIDE.globals.set('SK', 'a'.repeat(64));
    const j = await window.PYODIDE.runPythonAsync(`
import json, os
os.environ['TRUTHCERT_HMAC_KEY'] = SK
from impossible_ma.truthcert import sign_bundle, verify_bundle
b = sign_bundle(SP)
verify_bundle(b)
json.dumps(b, default=float)
    `);
    cb(j);
  } catch(e) {
    cb(JSON.stringify({error: String(e)}));
  }
})();
""")
    bundle = _json.loads(bundle_json)
    assert "error" not in bundle, f"TruthCert round-trip failed: {bundle.get('error')}"
    assert bundle["alg"] == "HMAC-SHA256", f"Unexpected alg: {bundle.get('alg')!r}"
    assert len(bundle["signature"]) == 64, (
        f"Expected 64-char hex signature, got length {len(bundle.get('signature',''))}"
    )


def test_printable_report_opens_new_window(page):
    # Load and run k=1
    Select(page.find_element(By.ID, "k1-dataset")).select_by_value("rare_hf")
    page.find_element(By.ID, "k1-load").click()
    WebDriverWait(page, 5).until(
        lambda d: not d.find_element(By.ID, "k1-run").get_attribute("disabled")
    )
    page.find_element(By.ID, "k1-run").click()
    WebDriverWait(page, 60).until(
        lambda d: d.execute_script("return window.K1_LAST_ENVELOPE != null")
    )
    initial = set(page.window_handles)
    page.find_element(By.ID, "k1-export-report").click()
    WebDriverWait(page, 10).until(
        lambda d: len(set(d.window_handles) - initial) >= 1
    )
    new_handle = list(set(page.window_handles) - initial)[0]
    page.switch_to.window(new_handle)
    # Wait for content to be written
    WebDriverWait(page, 10).until(
        lambda d: d.execute_script(
            "return document.readyState === 'complete' && "
            "document.body && document.body.textContent.length > 0"
        )
    )
    title = page.execute_script("return document.title;")
    body_text = page.execute_script("return document.body.textContent;")
    assert "ImpossibleMA report" in title or "ImpossibleMA report" in body_text, (
        f"Report title/body missing 'ImpossibleMA report'. title={title!r}"
    )
    assert "k1" in body_text.lower(), (
        f"Expected 'k1' in report body, got snippet: {body_text[:200]!r}"
    )
    # Close new window and switch back
    page.close()
    page.switch_to.window(list(initial)[0])


def test_raw_json_viewer_toggles(page):
    Select(page.find_element(By.ID, "k1-dataset")).select_by_value("rare_hf")
    page.find_element(By.ID, "k1-load").click()
    WebDriverWait(page, 5).until(
        lambda d: not d.find_element(By.ID, "k1-run").get_attribute("disabled")
    )
    page.find_element(By.ID, "k1-run").click()
    WebDriverWait(page, 45).until(
        lambda d: d.execute_script("return window.K1_LAST_ENVELOPE != null")
    )
    details = page.find_element(By.CSS_SELECTOR, "#k1-result details")
    initial_open = details.get_attribute("open")
    details.click()
    after_open = details.get_attribute("open")
    assert initial_open != after_open


def test_python_traceback_shown_in_error_pane(page):
    # Force invalid input that passes JS validation but fails in Python:
    # a target_se that the JS form-validator lets through but KoneInput raises on
    # (target_se <= 0). JS validator already blocks this, so we bypass by directly
    # invoking k1Run after planting bad Python-visible state.
    page.execute_script(r"""
        document.getElementById('k1-target-est').value = '-0.4';
        document.getElementById('k1-target-se').value = '-0.1';
        if (typeof k1AddRow === 'function') {
            const tbody = document.querySelector('#k1-adjacent tbody');
            tbody.innerHTML = '';
            k1AddRow('A', -0.3, 0.15);
            k1AddRow('B', -0.25, 0.12);
            k1AddRow('C', -0.4, 0.18);
        }
    """)
    # JS validator will disable the button; force the handler directly
    page.execute_script("k1Run();")
    WebDriverWait(page, 15).until(
        lambda d: not d.find_element(By.ID, "k1-error").get_attribute("hidden")
    )
    err = page.find_element(By.ID, "k1-error").text
    assert err.lower().startswith("error") or "target_se" in err or "positive" in err
