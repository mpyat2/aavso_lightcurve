# AAVSO Light Curve Viewer

A small, self-contained web page that downloads observations from the
**AAVSO International Database (AID)** and plots an interactive light curve,
either against time (JD or, on request, HJD) or phase-folded with a given
period and epoch.

It queries the same VSX web service (`view=api.object`) that
[VStar](https://github.com/AAVSO/VStar) uses for its "AAVSO International
Database" observation source, with the same request parameters and paging.

## Files

| File | Purpose |
|------|---------|
| `aavso_lightcurve_en.html` | The application, English interface |
| `aavso_lightcurve.html` | The same application, Ukrainian interface |
| `aavso_proxy.py` | Page server + CORS proxy for VSX; runs locally or on Cloud Run (Python standard library only) |
| `Dockerfile`, `.dockerignore` | Container for deploying `aavso_proxy.py` with the pages to Google Cloud Run |
| `cloudflare_worker.js` | Alternative CORS proxy as a Cloudflare Worker |
| `README.md` | This description |

Keep all files in the same folder.

## Quick start

```bash
python aavso_proxy.py          # default port 8765
python aavso_proxy.py 9000     # or choose another port
```

The browser opens automatically:

- English: <http://localhost:8765/>
- Ukrainian: <http://localhost:8765/uk>

Stop the server with **Ctrl+C**.

When run on your computer the proxy listens on `127.0.0.1` only. In every
mode it forwards only `view=api.object` requests to VSX.

## Which endpoint the page uses (and when a proxy is needed)

Browsers allow a page to read data from another site only if that site
sends CORS headers. `vsx.aavso.org` currently does (confirmed with the page
hosted on a free static web host), so the page normally talks to VSX
**directly**, whether it is opened as a file or served from any web host.
A proxy (`aavso_proxy.py`, Cloud Run, Cloudflare Worker) is only a fallback
in case direct requests are ever blocked.

The page picks its **API endpoint** in this order:

1. `?api=URL` in the page address, e.g.
   `…/aavso_lightcurve_en.html?api=https://my-proxy.example/vsx`;
2. a URL typed into **Connection → API endpoint** (saved in this browser;
   **Auto** forgets it);
3. `CONFIG_API` set in the HTML file (see below);
4. `/vsx`, if the page is served by `aavso_proxy.py` (detected via
   `/vsx/ping`);
5. otherwise `https://vsx.aavso.org/index.php` directly.

The line under the field shows which rule was used, and **Test** checks the
endpoint with a small request. A saved relative endpoint such as `/vsx` is
ignored when the server has no proxy, and if any non-direct endpoint fails
during loading, the page automatically switches to direct VSX and says so.

## Hosting the page on a web server

Just upload `aavso_lightcurve_en.html` and/or `aavso_lightcurve.html` to any
static web host; nothing else is needed. If a browser shows an old endpoint
after an update, reload with **Ctrl+F5** or press **Auto** under Connection.

### Optional: your own proxy

Only needed if direct requests to VSX stop working. Free hosts often block
outgoing connections from PHP/CGI, so put the proxy elsewhere:

1. Deploy a proxy: Google Cloud Run (A) or a Cloudflare Worker (B).
2. In the HTML file(s), near the top of the `<script>`, set

   ```js
   const CONFIG_API = "https://<your-proxy>/vsx";
   ```

3. Upload the HTML file(s) to the host. Every visitor then uses your proxy
   automatically.

Without step 2 you can still pass `?api=…` in the link or type the URL in
the Connection field.

#### A. Google Cloud Run

From the folder with the files (needs the `gcloud` CLI and a project with
billing enabled; light use stays within the free tier):

```bash
gcloud run deploy aavso-lightcurve \
    --source . \
    --project <PROJECT_ID> --region europe-west1 \
    --allow-unauthenticated --max-instances 2
```

Cloud Build builds the image from `Dockerfile`; the proxy listens on
`$PORT`. The command prints the service URL, e.g.
`https://aavso-lightcurve-xxxxxxxxxx.europe-west1.run.app`. Then:

- `https://…run.app/` and `…/uk` serve the pages themselves (no other host
  needed);
- `https://…run.app/vsx` is the endpoint for `CONFIG_API` on other hosts;
- `https://…run.app/vsx/ping` should answer `aavso_proxy v4`.

#### B. Cloudflare Worker

Free plan, no server to maintain:

1. <https://dash.cloudflare.com> → **Workers & Pages** → **Create** →
   *Hello World* worker; give it a name.
2. **Edit code**, replace everything with `cloudflare_worker.js`, **Deploy**.
3. The endpoint is `https://<name>.<account>.workers.dev/vsx`;
   `…/vsx/ping` should answer `aavso_proxy worker`.

## Using the page

1. **Star name**: any identifier VSX recognises, e.g. `SS Cyg`, `R Leo`,
   `V405 Dra`, or an AUID such as `000-BCP-220`. The star is looked up in
   VSX first; its name, AUID, variability type, period, spectral type and
   coordinates are shown above the plot.
2. **Minimum JD / Maximum JD**: the time range. The calendar date (UT) is
   shown under each field. By default the page opens with the **last 2
   years**, so popular stars do not start with a very long download. The
   quick buttons set the last 30 days, 1 year, 2 years or 10 years (the
   selected one is highlighted); **All** clears both fields and downloads the
   full history. Fill in both fields or leave both empty.
3. **Bands**: select one or more passbands. The list uses AID band codes
   with VStar's colours, e.g.:

   | Code | Band | Code | Band |
   |------|------|------|------|
   | `Vis.` | Visual | `CV` | Unfiltered, V zero point |
   | `V` | Johnson V | `CR` | Unfiltered, R zero point |
   | `B` | Johnson B | `TG` | Tri-Color Green |
   | `R` | Cousins R | `SG`, `SR`, `SI` | Sloan g, r, i |
   | `I` | Cousins I | `GG` | Gaia G |

   The *Vis. + V* button restores the default selection.
4. **Observer codes** (optional): load only observations by the given AAVSO
   observers. Codes may be separated by commas, spaces or semicolons and
   are converted to upper case; leave the field empty for all observers. As
   in VStar, they are sent as `&obscode=<code1>,<code2>`. The codes
   are added to the status line and to the CSV file name.
5. Click **Load**. Data are downloaded page by page (10 000 observations
   per request by default) with a progress counter, and the plot is updated
   as pages arrive. **Stop** cancels the download and keeps what has been
   received.

### Plot

- Interactive [Plotly](https://plotly.com/javascript/) chart (zoom, pan,
  PNG export from the toolbar); magnitude axis inverted.
- The time axis shows **JD − 2400000** (or HJD − 2400000) by default;
  untick *Time axis: JD − 2400000* to show full JD. Tick labels get as many
  decimals as the zoom level needs (from whole days down to 10⁻⁶ d,
  ≈0.1 s). Hover boxes always show the full JD/HJD.
- Hovering a point shows JD, calendar date, magnitude ± uncertainty,
  observer code, observation type and comment.
- Display options (applied instantly, no reload):
  - **Fainter-than**: upper limits, drawn as open ▼ triangles;
  - **Discrepant**: observations with validation flag `D` or `T`, drawn as ×
    (hidden by default);
  - **Error bars**.
- Click legend entries to hide/show individual series.

### JD → HJD conversion

AID times are Julian Dates (geocentric UTC). Tick **Convert JD → HJD** to
apply the heliocentric light-time correction to every observation.

- **RA (J2000)** and **Dec (J2000)** in degrees are filled in from VSX when
  a new star is loaded and can be edited.
- The correction is computed as in VStar (`J2000HJDConverter`, Meeus,
  *Astronomical Algorithms*, ch. 24):

  ```
  HJD = JD − (R / c) · [sin δ sin δ☉ + cos δ cos δ☉ cos(α − α☉)]
  ```

  where R is the Earth–Sun distance (AU), c = 173.1446 AU/day and α☉, δ☉
  are the Sun's J2000 coordinates. The JavaScript port reproduces the
  reference values in VStar's unit tests (BAA HJD calculator) to better
  than 0.1 s, and agrees with astropy to ~0.01 s.
- The hint shows the range of corrections for the loaded data
  (at most ±8.3 min).
- HJD is used everywhere at once: the time axis (titled *HJD*), phase
  folding (the epoch is then taken as an HJD), hover boxes (both JD and
  HJD are shown) and CSV export (an `HJD` column is added).
- Turning it off restores the original JD values; no data are reloaded.
- The **Minimum/Maximum JD** download range always refers to JD.

Epochs in VSX are usually given in HJD, so for accurate folding of
short-period stars enable HJD; the phase hint reminds you of this.

### Phase-folded curve

Switch **X axis** from *Time (JD)* to *Phase*.

- **Period, days** and **Epoch, JD** are filled in automatically from VSX
  when a new star is loaded. If VSX gives a period but no epoch, the JD of
  the brightest (non fainter-than) observation is used as the epoch; the
  hint under the fields says where the values came from.
- Both values can be edited freely; the plot is re-folded instantly, with no
  new download, and the current zoom is kept while you fine-tune them.
  Values you enter are kept when you reload the same star (e.g. with other
  bands or another JD range); **Use P and E from VSX** restores the
  catalogue values.
- Phase is computed as in VStar:

  ```
  phase = frac((t − E) / P),   0 ≤ phase < 1
  ```

  where t is JD, or HJD when the conversion is on. Each point is also plotted at `phase − 1` (previous cycle) when that
  falls in the selected **Phase range**: −1 … 1 (default, as in VStar),
  −0.5 … 1, or 0 … 1.
- The hover box shows the phase, cycle number (E-number), JD and the other
  observation details.
- If the period or epoch is missing or invalid, the time plot is shown and
  the hint asks for the values.

### Links with settings (page address parameters)

Settings can be passed in the page address, so a link can open the page
with a star, bands and range already selected and, with `load=1`, load the
data immediately:

```
https://mpyat2.github.io/aavso_lightcurve/aavso_lightcurve_en.html?star=V405+Dra&bands=V,CV&from=2460000&to=2461000&obscode=ABC&load=1
```

| Parameter | Meaning |
|-----------|---------|
| `star` | Star name or AUID; a space is written as `+` or `%20` |
| `bands` | Band codes separated by commas, e.g. `Vis.,V,CV` (case and the trailing dot of `Vis.` are optional) |
| `from`, `to` | JD range (both needed) |
| `days` | Last N days instead of `from`/`to`; `days=0` = all data |
| `obscode` | Observer codes separated by commas |
| `load=1` | Load the data as soon as the page opens |
| `x=phase` | Show the phase-folded curve |
| `period`, `epoch` | Period (days) and epoch for folding; kept instead of the VSX values |
| `hjd=1` | Convert JD → HJD |
| `jd=full` | Full JD on the time axis instead of JD − 2400000 |
| `api` | API endpoint (see *Which endpoint the page uses*) |

Without `from`/`to`/`days` the default range (last 2 years) is used.
Unknown band codes or an invalid range are reported and nothing is loaded.

The **Link** button builds such an address from the current settings and
copies it to the clipboard (on plain-http hosts, where browsers do not allow
this, it is shown for copying by hand). A range chosen with a quick button
is stored as `days=N`, so the link always shows the latest data.

### Export

**Save CSV** writes the loaded observations to
`<star>_aid.csv` with the columns:

```
JD,mag,uncert,band,by,fainterThan,val,obsType,obsID,comment
```

When JD → HJD conversion is on, an `HJD` column is added; when a valid
period and epoch are set, a `phase` column (0 … 1) is added.

### Connection settings

Under **Connection**:

- **API endpoint**: chosen automatically (see *Why a proxy, and which
  endpoint the page uses*); can be overridden. **Test** checks it, **Auto**
  returns to automatic selection.
- **Observations per request page**: 100–50 000 (VStar uses 50 000).

## How it works

1. `index.php?view=api.object&ident=<name>` returns the VSX object record
   (`<VSXObject>`), from which the AUID is taken.
2. Observations are requested with

   ```
   index.php?view=api.object&ident=<AUID>&data=<N>&csv
            &band=<b1,b2,…>&mtype=std[&fromjd=<min>&tojd=<max>]
            [&obscode=<c1,c2,…>]&page=<k>
   ```

   Each response is XML with a `<Count>` element (total number of
   observations) and the CSV data inside a `<Data>` CDATA section. Pages are
   requested until the count is reached or an empty page is returned.
3. The CSV is parsed in the browser (quoted fields with commas are handled)
   and plotted, one trace per band.

Only standardised magnitudes (`mtype=std`) are requested, as in VStar.

## Requirements

- A modern browser (Chrome, Firefox, Edge, Safari).
- Internet access to `vsx.aavso.org` (directly or via a proxy) and to
  `cdn.plot.ly`, which hosts the plotting library.
- Python 3.7+ for `aavso_proxy.py` (no third-party packages).

## Notes and limitations

- Very long histories of popular stars (hundreds of thousands of
  observations) take a while to download; narrow the JD range or bands if
  needed. Rendering uses WebGL, so large data sets stay responsive.
- By default times are plotted and folded as JD exactly as stored in AID.
  The optional HJD conversion is heliocentric (not barycentric) and uses
  geocentric UTC, as VStar does; the HJD–BJD_TDB difference (about a minute,
  mostly TT−UTC) is not applied.
- Please follow the AAVSO data-use and acknowledgement guidelines when you
  publish results based on AID data.

## Credits

Data: AAVSO International Database and VSX, <https://www.aavso.org/>.
The API usage follows VStar (AGPL-3.0), <https://github.com/AAVSO/VStar>.
