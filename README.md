# Open Targets statistics

Install the Python dependencies with `uv sync`.

## Run in VS Code

Open this folder (`ot-stats`) in VS Code. In the Command Palette
(`Cmd+Shift+P`), run **Python: Select Interpreter** and choose
`.venv/bin/python` from this project. If necessary, use **Enter interpreter
path** and select `/Users/leimane/Code/ot-stats/.venv/bin/python`.

Open `main.py` and click **Run Python File** in the top-right corner, or press
F5 to run the configured debugger. Set a breakpoint on the first print inside
`main()` to pause after both DataFrames have loaded and inspect local variables.

## Browse DataFrames interactively

Use the Microsoft Python, Jupyter, and Data Wrangler extensions (recommended
by this workspace).

1. Open `explore.py` and click **Run Cell** above the first `# %%` line.
2. If prompted for a kernel, select the project's `.venv` Python environment.
3. In the Python Interactive window, click **Variables** to see `phenotypes_df`
   and `analytics_df`.
4. Use the Data Wrangler button beside either DataFrame to open its full table
   for scrolling, filtering, and sorting.

The DataFrames stay available in the interactive session until you restart
the kernel. The `.head()` cells provide small previews; the table viewer opens
the full DataFrame. Run the first cell again after changing the input files.
