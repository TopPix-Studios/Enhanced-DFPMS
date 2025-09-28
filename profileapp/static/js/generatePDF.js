function generatePDF({ title, chartImageData, filters, tableHeaders, tableData, fileName, breakdowns = null }) {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.width;
    const currentDate = new Date();
    const dateOptions = { year: 'numeric', month: 'long', day: 'numeric' };
    const formattedDate = currentDate.toLocaleDateString('en-US', dateOptions); // "May 26, 2025"

    // Header Logos and Text
    const leftLogoUrl = "/static/img/General_Santos_City_seal_2.jpg";
    const rightLogoUrl = "/static/img/DarkBlue/dark blue.png";
    const logoWidth = 20;
    const logoHeight = 20;
    const headerText = [
        'Republic of the Philippines',
        'General Santos City',
        'CITY ECONOMIC MANAGEMENT AND COOPERATIVE',
        'DEVELOPMENT OFFICE'
    ];

    const tableStyleOptions = {
        theme: 'grid',
        styles: {
            font: 'times',
            fontSize: 10
        },
        headStyles: {
            fillColor: '#1E3A8A',
            textColor: '#FFFFFF',
            fontStyle: 'bold'
        },
        alternateRowStyles: {
            fillColor: '#E8F0FE'
        }
    };


    const headerYStart = 10;
    const lineSpacing = 5;

    doc.addImage(leftLogoUrl, 'PNG', 10, headerYStart, logoWidth, logoHeight);
    doc.addImage(rightLogoUrl, 'PNG', pageWidth - logoWidth - 10, headerYStart, logoWidth, logoHeight);

    doc.setFont('times', 'bold');
    doc.setFontSize(12);
    headerText.forEach((line, index) => {
        const textWidth = doc.getTextWidth(line);
        doc.text(line, (pageWidth - textWidth) / 2, headerYStart + (index + 1) * lineSpacing);
    });

    const reportTitle = `${title} as of ${formattedDate}`;
    // e.g., "Skills Report as of May 26, 2025"

    doc.setFontSize(16);
    doc.text(reportTitle, 15, headerYStart + (headerText.length + 1) * lineSpacing + 10);

    const chartYStart = headerYStart + (headerText.length + 1) * lineSpacing + 20;
    if (chartImageData) {
        doc.addImage(chartImageData, 'PNG', 15, chartYStart, 180, 90);
    }

    const filtersYStart = chartYStart + 100;
    doc.setFontSize(12);
    const filtersWidth = doc.getTextWidth(filters);
    doc.text(filters, (pageWidth - filtersWidth) / 2, filtersYStart);

    const tableYStart = filtersYStart + 10;
    const totalIndex = 1; // Change this to the index of your numeric column
    const totalValue = tableData.reduce((sum, row) => sum + (parseFloat(row[totalIndex]) || 0), 0);

    // Build total row
    const totalRow = tableHeaders.map((_, idx) => {
        if (idx === 0) return "Total";
        if (idx === totalIndex) return totalValue.toString();
        return "";
    });
    doc.autoTable({
        head: [tableHeaders],
        body: [...tableData, totalRow],
        startY: tableYStart,
        ...tableStyleOptions,
        didParseCell: function (data) {
            const row = data.row.raw;
            const isTotalRow = row?.[0] === "Total";

            if (isTotalRow) {
                data.cell.styles.fontStyle = 'bold';
                data.cell.styles.fillColor = [220, 230, 241]; // light blue
                data.cell.styles.textColor = [0, 0, 0]; // ensure text is readable
            }
        }

    });



    // Optional Breakdown Section
    if (breakdowns && (breakdowns.gender || breakdowns.barangay || breakdowns.age)) {
        let currentY = doc.lastAutoTable.finalY + 15;

        // Section Header
        doc.setFont('times', 'bold');
        doc.setFontSize(14);
        doc.text("Breakdown per Category", 15, currentY);
        doc.setLineWidth(0.5);
        doc.line(15, currentY + 2, pageWidth - 15, currentY + 2); // underline
        currentY += 8;

        tableData.forEach(([key]) => {
            const genders = breakdowns.gender?.[key] || {};
            const barangays = breakdowns.barangay?.[key] || {};
            const ageGroups = breakdowns.age?.[key] || {};

            // Category Title
            doc.setFont('times', 'bold');
            doc.setFontSize(12);
            doc.text(`Category: ${key}`, 20, currentY);
            currentY += 5;

            const breakdownTables = [
                {
                    title: "Gender",
                    data: genders,
                    headers: ['Gender', 'Count']
                },
                {
                    title: "Barangay",
                    data: barangays,
                    headers: ['Barangay', 'Count']
                },
                {
                    title: "Age Group",
                    data: ageGroups,
                    headers: ['Age Group', 'Count']
                }
            ];

            for (const { title, data, headers } of breakdownTables) {
                if (Object.keys(data).length > 0) {
                    const entries = Object.entries(data);
                    const total = entries.reduce((sum, [, count]) => sum + count, 0);
                    const body = [...entries.map(([k, v]) => [k, v]), ["Total", total]];

                    doc.autoTable({
                        startY: currentY + 4,
                        head: [headers],
                        body: body,
                        margin: { left: 15, right: 15 },
                        ...tableStyleOptions,
                        didParseCell: function (data) {
                            const row = data.row.raw;
                            const isTotalRow = row?.[0] === "Total";

                            if (isTotalRow) {
                                data.cell.styles.fontStyle = 'bold';
                                data.cell.styles.fillColor = [220, 230, 241];
                                data.cell.styles.textColor = [0, 0, 0];
                            }
                        }
                    });

                    currentY = doc.lastAutoTable.finalY + 8;

                    // Add new page if near the bottom
                    if (currentY > 270) {
                        doc.addPage();
                        currentY = 20;
                    }
                }
            }

            // Visual spacing between categories
            currentY += 5;
            if (currentY > 270) {
                doc.addPage();
                currentY = 20;
            }
        });
    }


    // Signatory Section: "Prepared by", Blank Line, Date
    let signatoryStartY = doc.lastAutoTable ? doc.lastAutoTable.finalY + 25 : 250;
    if (signatoryStartY > 250) {
        doc.addPage();
        signatoryStartY = 40;
    }
    doc.setFont('times', 'normal');
    doc.setFontSize(12);

    // Add "Prepared by:" label
    doc.text("Prepared by:", 60, signatoryStartY);

    // Blank line for signature
    doc.text("_________________________", 60, signatoryStartY + 8);

    // Date line (optional: use today's date)

    doc.text(`Date: ${formattedDate}`, 60, signatoryStartY + 16);

    doc.save(fileName);
}
