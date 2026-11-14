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
| `aavso_proxy.py` | Optional local server/proxy (Python standard library only) |
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

### Without the proxy

You can also open the HTML file directly (double-click). The page then calls
`https://vsx.aavso.org/index.php` from the browser. If AAVSO does not send
CORS headers allowing this, the browser blocks the request and the page
shows an error suggesting the proxy. `aavso_proxy.py` avoids the problem:
it serves the page and forwards `/vsx?…` requests to VSX from Python, where
CORS does not apply.

The proxy listens on `127.0.0.1` only and forwards only `view=api.object`
requests.

## Using the page

1. **Star name**: any identifier VSX recognises, e.g. `SS Cyg`, `R Leo`,
   `V405 Dra`, or an AUID such as `000-BCP-220`. The star is looked up in
   VSX first; its name, AUID, variability type, period, spectral type and
   coordinates are shown above the plot.
2. **Minimum JD / Maximum JD**: the time range. The calendar date (UT) is
   shown under each field. The quick buttons set the last 30 days, 1 year or
   10 years; **All** clears both fields and downloads the full history. Fill
   in both fields or leave both empty.
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
4. Click **Load**. Data are downloaded page by page (10 000 observations
   per request by default) with a progress counter, and the plot is updated
   as pages arrive. **Stop** cancels the download and keeps what has been
   received.

### Plot

- Interactive [Plotly](https://plotly.com/javascript/) chart (zoom, pan,
  PNG export from the toolbar); magnitude axis inverted.
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

- **API endpoint**: `/vsx` when the page is served by `aavso_proxy.py`,
  `https://vsx.aavso.org/index.php` when opened as a file. Can be changed
  manually.
- **Observations per request page**: 100–50 000 (VStar uses 50 000).

## How it works

1. `index.php?view=api.object&ident=<name>` returns the VSX object record
   (`<VSXObject>`), from which the AUID is taken.
2. Observations are requested with

   ```
   index.php?view=api.object&ident=<AUID>&data=<N>&csv
            &band=<b1,b2,…>&mtype=std[&fromjd=<min>&tojd=<max>]&page=<k>
   ```

   Each response is XML with a `<Count>` element (total number of
   observations) and the CSV data inside a `<Data>` CDATA section. Pages are
   requested until the count is reached or an empty page is returned.
3. The CSV is parsed in the browser (quoted fields with commas are handled)
   and plotted, one trace per band.

Only standardised magnitudes (`mtype=std`) are requested, as in VStar.

## Requirements

- A modern browser (Chrome, Firefox, Edge, Safari).
- Internet access to `vsx.aavso.org` and to `cdn.plot.ly`, which hosts the
  plotting library.
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
