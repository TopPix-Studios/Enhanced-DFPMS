function generateEventPDF({ title, charts, insights, fileName }) {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();

    const pageWidth = doc.internal.pageSize.width;
    const pageHeight = doc.internal.pageSize.height;

    // Header Logos and Text
    const leftLogoUrl = "/static/img/bp-logo.png"; // Left logo path
    const rightLogoUrl = "/static/img/DarkBlue/dark blue.png"; // Right logo path

    const logoWidth = 20;
    const logoHeight = 20;

    const headerText = [
        "Republic of the Philippines",
        "General Santos City",
        "CITY ECONOMIC MANAGEMENT AND COOPERATIVE",
        "DEVELOPMENT OFFICE",
    ];

    const headerYStart = 10; // Starting Y position for header
    const lineSpacing = 5; // Spacing between lines in the header

    // Add Header Content
    getBase64ImageFromURL(leftLogoUrl, function (leftLogoBase64) {
        getBase64ImageFromURL(rightLogoUrl, function (rightLogoBase64) {
            // Add Left Logo
            const marginLeft = 10;
            doc.addImage(leftLogoBase64, "PNG", marginLeft, headerYStart, logoWidth, logoHeight);

            // Add Right Logo
            const marginRight = 10;
            doc.addImage(rightLogoBase64, "PNG", pageWidth - logoWidth - marginRight, headerYStart, logoWidth, logoHeight);

            // Add Header Text
            doc.setFont("times", "bold");
            doc.setFontSize(12);
            headerText.forEach((line, index) => {
                const textWidth = doc.getTextWidth(line);
                doc.text(line, (pageWidth - textWidth) / 2, headerYStart + (index + 1) * lineSpacing);
            });

            // Add Chart Title
            const currentDate = new Date().toLocaleDateString();
            const reportTitle = `${title} (${currentDate})`;
            doc.setFontSize(16);
            doc.setFont("times", "bold");
            const chartTitleY = headerYStart + (headerText.length + 1) * lineSpacing + 10;
            doc.text(reportTitle, 15, chartTitleY);

            let currentYPosition = chartTitleY + 20;

            // Add Charts and Tables
            charts.forEach((chart, index) => {
                const chartCanvas = document.getElementById(chart.id);
                if (chartCanvas) {
                    const chartImage = chartCanvas.toDataURL("image/png");

                    // Add Chart Title
                    doc.setFontSize(12);
                    doc.text(chart.label, 15, currentYPosition);

                    // Add Chart and Table Side by Side
                    const chartX = 15; // Left margin for the chart
                    const tableX = 110; // Starting X position for the table

                    // Add Chart Image
                    doc.addImage(chartImage, "PNG", chartX, currentYPosition + 5, 80, 60);

                    // Add Table Data
                    const chartData = chart.data || [];
                    doc.autoTable({
                        head: [["Label", "Value"]],
                        body: chartData,
                        startY: currentYPosition + 5,
                        margin: { left: tableX },
                        tableWidth: 90, // Adjust table width to fit the space
                        theme: "grid",
                        headStyles: {
                            fillColor: [54, 162, 235],
                            textColor: [255, 255, 255],
                        },
                        bodyStyles: {
                            fillColor: [227, 242, 253],
                            textColor: [0, 0, 0],
                        },
                    });

                    currentYPosition += 70; // Move Y position down after chart and table

                    // Check if the next chart or table will fit on the page
                    if (currentYPosition + 50 > pageHeight) {
                        doc.addPage();
                        currentYPosition = 10;
                    }
                }
            });

            // Add Insights Table at the End
            if (currentYPosition + 50 > pageHeight) {
                doc.addPage();
                currentYPosition = 10;
            }

            doc.setFontSize(16);
            doc.text("Event Insights Summary", 15, currentYPosition);

            doc.autoTable({
                head: [["Insight", "Value"]],
                body: insights,
                startY: currentYPosition + 10,
                theme: "grid",
                headStyles: {
                    fillColor: [54, 162, 235],
                    textColor: [255, 255, 255],
                },
                bodyStyles: {
                    fillColor: [227, 242, 253],
                    textColor: [0, 0, 0],
                },
                margin: { left: 15, right: 15 },
            });

            // Save the PDF
            doc.save(fileName);
        });
    });
}

// Helper function to load images as Base64
function getBase64ImageFromURL(url, callback) {
    const img = new Image();
    img.setAttribute("crossOrigin", "anonymous"); // Prevent CORS issues
    img.onload = function () {
        const canvas = document.createElement("canvas");
        canvas.width = this.width;
        canvas.height = this.height;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(this, 0, 0);
        const dataURL = canvas.toDataURL("image/png");
        callback(dataURL);
    };
    img.src = url;
}
