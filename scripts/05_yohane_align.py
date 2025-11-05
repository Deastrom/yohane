#!/usr/bin/env python3
"""
Step 6: Yohane Forced Alignment

Uses Yohane for syllable-level forced alignment with separated vocals.

Auto-detection priority (best to worst):
1. vocals_yohane.wav (from step 03 - desung, optimal for alignment)
2. Original vocals (from separation - fallback)

Generates clean ASS with karaoke timing.
"""

import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import typer
from rich.console import Console

# Add project root scripts/ to path
# Go up from tools/yohane/scripts to nfcu root
_root_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_root_dir / "scripts"))

if TYPE_CHECKING:
    from pipeline_state import (  # pyright: ignore[reportMissingImports]
        PipelineState as PipelineStateType,
    )
else:
    PipelineStateType = None

try:
    from pipeline_state import PipelineState  # pyright: ignore[reportMissingImports]
    PIPELINE_STATE_AVAILABLE = True
except ImportError as e:
    PipelineState = None  # type: ignore[assignment,misc]
    PIPELINE_STATE_AVAILABLE = False
    import warnings
    warnings.warn(f"pipeline_state not available: {e}")
    PipelineState = None  # type: ignore

app = typer.Typer()
console = Console()
logger = logging.getLogger(__name__)


@app.command()
def main(
    vocals_file: Optional[Path] = typer.Option(None, "--vocals", "-v", help="Vocals audio file (auto-detected from pipeline state if not provided)"),
    lyrics_file: Optional[Path] = typer.Option(None, "--lyrics", "-l", help="Lyrics text file (auto-detected from pipeline state if not provided)"),
    output_file: Optional[Path] = typer.Option(None, "--output", "-o", help="Output ASS file (auto-detected from pipeline state if not provided)"),
    language: str = typer.Option("en", "--language", help="Language code for alignment"),
    style: str = typer.Option("none", "--style", "-s", help="Subtitle style preset"),
):
    """
    Run Yohane forced alignment on vocals track

    Automatically detects best vocals file:
    1. vocals_yohane.wav (from step 03 - desung, best for alignment)
    2. Original vocals (from separation - fallback)
    """

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    console.print("\n[bold cyan]Yohane Forced Alignment[/bold cyan]\n")

    # Auto-detect files from pipeline state if not provided
    if PIPELINE_STATE_AVAILABLE and (vocals_file is None or lyrics_file is None or output_file is None):
        try:
            assert PipelineState is not None  # for type checker
            state = PipelineState(_root_dir)
            output_dir = Path(state.get_output_dir())

            if vocals_file is None:
                # Priority order: vocals_yohane.wav > original vocals
                # 1. Check for processed vocals (from step 03 - best for alignment)
                yohane_vocals = output_dir / "stems" / "vocals_yohane.wav"
                logger.info(f"Checking for yohane-processed vocals at: {yohane_vocals}")

                if yohane_vocals.exists():
                    vocals_file = yohane_vocals
                    console.print(f"[green]✓[/green] Using yohane-processed vocals: {vocals_file}")
                    logger.info(f"Using yohane-processed vocals (desung) for optimal alignment: {vocals_file}")
                else:
                    # 2. Fall back to original vocals from separation
                    logger.info("No processed vocals found, checking pipeline state for original vocals")
                    stems = state.get_stems()
                    logger.info(f"Stems from pipeline state: {stems}")
                    if not stems or not stems.get("vocals"):
                        console.print("[red]Error: No vocals file found in pipeline state[/red]")
                        raise typer.Exit(1)
                    vocals_file = Path(stems["vocals"])
                    console.print(f"[yellow]⚠[/yellow] Using original vocals: {vocals_file}")
                    console.print("[dim]Tip: Run step 03 (vocal_processing) for better alignment[/dim]")
                    logger.info(f"Using original vocals: {vocals_file}")

            if lyrics_file is None:
                lyrics_file = output_dir / "lyrics_raw_ytmusic.txt"
                if not lyrics_file.exists():
                    console.print(f"[red]Error: Lyrics file not found: {lyrics_file}[/red]")
                    console.print("[yellow]Tip: Run step 4 (fetch lyrics) first[/yellow]")
                    raise typer.Exit(1)
                logger.info(f"Using lyrics file: {lyrics_file}")

            if output_file is None:
                output_file = output_dir / "vocals.ass"
                logger.info(f"Output will be saved to: {output_file}")

        except Exception as e:
            console.print(f"[red]Error reading pipeline state: {e}[/red]")
            console.print("[yellow]Tip: Run previous steps first, or provide file paths manually[/yellow]")
            raise typer.Exit(1)
    elif vocals_file is None or lyrics_file is None:
        console.print("[red]Error: vocals_file and lyrics_file are required[/red]")
        console.print("[yellow]Usage: python 05_yohane_align.py --vocals vocals.wav --lyrics lyrics.txt[/yellow]")
        raise typer.Exit(1)

    # Validate input files
    if not vocals_file.exists():
        console.print(f"[red]Error: Vocals file not found: {vocals_file}[/red]")
        raise typer.Exit(1)

    if not lyrics_file.exists():
        console.print(f"[red]Error: Lyrics file not found: {lyrics_file}[/red]")
        raise typer.Exit(1)

    console.print(f"Vocals: [green]{vocals_file}[/green]")
    console.print(f"Lyrics: [green]{lyrics_file}[/green]")
    console.print(f"Language: [yellow]{language}[/yellow]\n")

    # Load lyrics text
    try:
        with open(lyrics_file, "r", encoding="utf-8") as f:
            lyrics_text = f.read()
    except Exception as e:
        console.print(f"[red]Error reading lyrics file:[/red] {e}")
        raise typer.Exit(1)

    # Run yohane using library API
    console.print("[cyan]Running Yohane alignment...[/cyan]")
    logger.info(f"Loading Yohane with language={language}")

    try:
        from yohane import Yohane

        # Validate language parameter
        if language not in ("ja", "en"):
            console.print(f"[red]Error: Invalid language '{language}'. Must be 'ja' or 'en'[/red]")
            raise typer.Exit(1)
        
        # Create Yohane instance without separator (we already have vocals)
        yohane = Yohane(separator=None, language=language)  # type: ignore[arg-type]

        # Load vocals audio
        logger.info(f"Loading vocals: {vocals_file}")
        yohane.load_song(vocals_file)

        # Load lyrics text
        logger.info("Loading lyrics")
        yohane.load_lyrics(lyrics_text)

        # Perform forced alignment
        logger.info("Performing forced alignment...")
        yohane.force_align()

        # Generate subtitle file
        logger.info("Generating subtitle file...")
        subs = yohane.make_subs()

        # Save to output location
        if output_file is None:
            output_file = vocals_file.parent / f"{vocals_file.stem}.ass"

        output_file.parent.mkdir(parents=True, exist_ok=True)
        subs.save(str(output_file))

        console.print(f"[green]✓[/green] ASS file created: {output_file}")
        logger.info(f"Saved: {output_file}")

        # Update pipeline state
        if PIPELINE_STATE_AVAILABLE:
            try:
                assert PipelineState is not None  # for type checker
                state = PipelineState(_root_dir)
                state.set_alignment(
                    ass_file=str(output_file),
                    vocals_used=str(vocals_file),
                    lyrics_used=str(lyrics_file)
                )
                logger.info("Pipeline state updated")
                console.print("[dim]Pipeline state updated[/dim]")
            except Exception as e:
                logger.warning(f"Could not update pipeline state: {e}")

        console.print(f"\n[green]✓[/green] Complete! Output: {output_file}\n")

    except Exception as e:
        console.print(f"[red]Error running Yohane:[/red] {e}")
        logger.exception("Yohane alignment failed")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
