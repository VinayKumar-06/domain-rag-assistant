# Interface images

The Streamlit interface uses a project-local hero illustration at
`assets/research-assistant-hero.webp`. It is displayed beside the page heading and followed by
three text cards that explain the user flow. Keeping the asset in the repository makes it
available in local runs, Docker builds, and hosted deployments without relying on a third-party
image URL.

## Replace or add a hero image

1. Choose an image you own or have permission to use. A wide image around 3:2 or 16:9 works well;
   compress it so the repository and page load stay lightweight.
2. Save it under `assets/`, for example `assets/research-assistant-hero.webp`.
3. Update the `HERO_IMAGE` filename in `ui/streamlit_app.py`. Keep the path rooted at the app
   file's parent directory:

   ```python
   HERO_IMAGE = Path(__file__).resolve().parents[1] / "assets" / "research-assistant-hero.webp"
   ```

4. Change the image caption or the three onboarding card labels in the same file if needed. The
   cards are ordinary Streamlit components and require no extra package.
5. Start the API and UI using the Quick start commands in the main README. Confirm the image is
   visible next to the title and that the three cards fit at desktop and narrow browser widths.
6. Include the image file and its code change in the same Git commit. Verify the deployment build
   contains the `assets/` directory; do not depend on local-only files or temporary URLs.

## Troubleshooting

- **Image not found:** check that the filename and extension in `HERO_IMAGE` match exactly. Paths
  are resolved from the source file, not the shell's current directory.
- **Slow page load:** resize and compress the image before committing it. Prefer a few hundred KB
  over multi-megabyte originals.
- **Image is cropped or too tall:** use a wide composition with the main subject near the center;
  adjust the image itself rather than embedding essential text in it.
- **Docker or hosted build is missing it:** ensure the image is committed and not excluded by
  `.dockerignore` or the deployment's build context.

The generated hero image was created specifically for this project with no embedded text, logos,
or external image dependency.
