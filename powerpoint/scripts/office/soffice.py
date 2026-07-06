import sys
import os
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--convert-to", type=str)
    parser.add_argument("file", type=str)
    args = parser.parse_args()

    # The conversion requested is 'pdf' for a pptx file
    input_path = os.path.abspath(args.file)
    if not os.path.exists(input_path):
        print(f"File not found: {input_path}")
        sys.exit(1)

    print(f"Converting {input_path} to PDF using PowerPoint COM interface...")

    # Let's use PowerPoint to do the conversion
    import win32com.client
    powerpoint = win32com.client.Dispatch("Powerpoint.Application")
    powerpoint.Visible = True # PowerPoint requires to be visible sometimes for headless/automated run depending on environment

    try:
        deck = powerpoint.Presentations.Open(input_path, WithWindow=False)
        output_path = os.path.splitext(input_path)[0] + ".pdf"
        # 32 is the constant for PDF export format in PowerPoint COM model
        deck.SaveAs(output_path, 32)
        deck.Close()
        print(f"Successfully converted pptx to PDF at {output_path}")
    except Exception as e:
        print(f"Error during conversion: {e}")
        sys.exit(1)
    finally:
        powerpoint.Quit()

if __name__ == "__main__":
    main()
