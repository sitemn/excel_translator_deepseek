from gspread_helper import setup_gspread_client, append_row_to_sheet

def write_to_google_sheets(df, spreadsheet_id, credentials_path, logger):
    unmatched_rows = []

    try:
        gc = setup_gspread_client(credentials_path)
        sh = gc.open_by_key(spreadsheet_id)
        worksheet_titles = [ws.title for ws in sh.worksheets()]

        for _, row in df.iterrows():
            address_number = str(row['Address']).strip()

            # Find matching worksheet
            matched_title = next((title for title in worksheet_titles if address_number in title), None)

            if not matched_title:
                logger.warning(f"No worksheet found for address number: {address_number}")
                unmatched_rows.append(row)
                continue

            try:
                append_row_to_sheet(gc, spreadsheet_id, matched_title, row)
            except Exception as e:
                logger.error(f"Failed to write to '{matched_title}' for address '{address_number}': {e}")
                unmatched_rows.append(row)

        logger.info(f"✅ Finished writing to Google Sheets.")
        logger.info(f"❗ {len(unmatched_rows)} row(s) could not be matched to a worksheet.")

        return unmatched_rows

    except Exception as e:
        logger.error(f"Critical error during Google Sheets write: {e}")
        return df.to_dict('records')  # fallback: return all if major failure
