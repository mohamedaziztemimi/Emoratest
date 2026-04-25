const fs = require('fs');
const PDFParser = require('pdf2json');

const pdfPath = 'Emoratest refactroing playbook.md';
const outputPath = 'playbook_extracted.txt';

const pdfParser = new PDFParser();

pdfParser.on('pdfParser_dataError', errData => {
    console.error('Error:', errData.parserError);
});

pdfParser.on('pdfParser_dataReady', pdfData => {
    let text = '';

    // Extract text from all pages
    if (pdfData.Pages) {
        pdfData.Pages.forEach((page, pageNum) => {
            text += `\n=== PAGE ${pageNum + 1} ===\n`;

            if (page.Texts) {
                page.Texts.forEach(textItem => {
                    if (textItem.R) {
                        textItem.R.forEach(r => {
                            if (r.T) {
                                text += decodeURIComponent(r.T) + ' ';
                            }
                        });
                    }
                });
            }
        });
    }

    fs.writeFileSync(outputPath, text);
    console.log('PDF extracted to:', outputPath);
    console.log('Total characters:', text.length);
    console.log('\n=== FIRST 3000 CHARACTERS ===\n');
    console.log(text.substring(0, 3000));
});

fs.readFile(pdfPath, (err, pdfBuffer) => {
    if (err) {
        console.error('Error reading file:', err);
        return;
    }
    pdfParser.parseBuffer(pdfBuffer);
});
