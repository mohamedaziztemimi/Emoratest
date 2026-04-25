const fs = require('fs');
const { createWorker } = require('tesseract.js');
const PDFParser = require('pdf2json');

const pdfPath = 'Emoratest refactroing playbook.md';
const outputPath = 'playbook_text.txt';

async function extractTextFromPDF() {
    console.log('Starting OCR extraction...');

    // First, convert PDF to get page images
    const pdfParser = new PDFParser();

    const pages = await new Promise((resolve, reject) => {
        pdfParser.on('pdfParser_dataError', errData => reject(errData.parserError));
        pdfParser.on('pdfParser_dataReady', pdfData => {
            resolve(pdfData.Pages);
        });
        fs.readFile(pdfPath, (err, pdfBuffer) => {
            if (err) reject(err);
            pdfParser.parseBuffer(pdfBuffer);
        });
    });

    console.log(`Found ${pages.length} pages`);

    const worker = await createWorker('eng');
    let fullText = '';

    for (let i = 0; i < Math.min(5, pages.length); i++) {
        console.log(`Processing page ${i + 1}...`);

        const page = pages[i];

        // Try to extract form fields or get page dimensions
        try {
            // Get the text content that was already extracted (even if minimal)
            let pageText = '';

            if (page.Texts) {
                for (const textItem of page.Texts) {
                    if (textItem.R) {
                        for (const r of textItem.R) {
                            if (r.T) {
                                pageText += decodeURIComponent(r.T) + ' ';
                            }
                        }
                    }
                }
            }

            if (pageText.trim()) {
                fullText += `\n=== PAGE ${i + 1} (extracted) ===\n${pageText}\n`;
            }
        } catch (e) {
            console.error(`Error on page ${i + 1}:`, e.message);
        }
    }

    await worker.terminate();

    if (fullText.trim()) {
        fs.writeFileSync(outputPath, fullText);
        console.log(`\nText written to ${outputPath}`);
        console.log('=== EXTRACTED TEXT ===');
        console.log(fullText);
    } else {
        console.log('No text could be extracted. The PDF may be entirely image-based.');
        console.log('Consider using an OCR tool on each page image directly.');
    }
}

extractTextFromPDF().catch(console.error);
