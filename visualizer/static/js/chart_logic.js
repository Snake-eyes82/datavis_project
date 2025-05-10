// C:\Users\Jason\OneDrive\Desktop\datavisproject\visualizer\static\js\chart_logic.js

// Global variable to hold the chart instance so we can destroy/update it later
let myChart = null;

// Global variables to store original scale limits for the custom scrollbars
// These will be set when the chart is first created.
let originalXScaleMin = undefined;
let originalXScaleMax = undefined;
let originalYScaleMin = undefined; // Added for zoom scrollbar
let originalYScaleMax = undefined; // Added for zoom scrollbar


// Global variables for custom scrollbar handle dragging (Pan Bar)
let isDraggingPanHandle = false; // Renamed for clarity
let startPanHandleX; // X position where pan drag started
let startPanHandleLeft; // Initial left position of pan handle

// Global variables for custom scrollbar handle dragging (Zoom Bar)
let isDraggingZoomHandle = false; // Added for zoom bar
let startZoomHandleY; // Y position where zoom drag started
let startZoomHandleTop; // Initial top position of zoom handle


// References to scrollbar elements (assigned in window.onload)
let panScrollbarTrack;
let panScrollbarHandle;
let panScrollbarArrowLeft;
let panScrollbarArrowRight;

let zoomScrollbarTrack; // Added for zoom bar
let zoomScrollbarHandle; // Added for zoom bar
let zoomScrollbarArrowUp; // Added for zoom bar
let zoomScrollbarArrowDown; // Added for zoom bar

let isCanvasPanning = false;
let lastPanMouseX; // To store the mouse X position during canvas pan

let dataUnitsPerPixel = 0;
let panSpeedFactor = 1; // Adjust this value to control the overall pan speed

// Function to destroy the existing chart instance
function destroyChart() {
	if (myChart) {
		myChart.destroy();
		myChart = null; // Set to null after destroying to indicate no chart exists
		console.log("Debug in chart_logic.js: Existing chart destroyed.");

		// Reset original scale limits when chart is destroyed
		originalXScaleMin = undefined;
		originalXScaleMax = undefined;
		originalYScaleMin = undefined;
		originalYScaleMax = undefined;
		console.log("Debug: Original scale limits reset.");
	}
}

// Function to set the height of the chart container based on selector value
// This function exists, but with inline styles on #basicChartContainer, it won't be effective in this step.
function setChartContainerHeight(size) {
	const container = document.querySelector('.chart-container') || document.getElementById('basicChartContainer'); // Check for both potential containers
	if (container) {
		let height = 600; // Default height if size is unexpected

		switch(size) {
			case 'small': height = 400; break;
			case 'medium': height = 600; break;
			case 'large': height = 800; break;
			case 'xlarge': height = 1000; break;
			default: height = 600; // Fallback to default
		}
		// Note: This line sets the CSS height. If you are using inline styles on the container,
		// the inline style will have higher specificity and override this.
		// container.style.height = `${height}px`; // Commented out as we use inline style on basicChartContainer for now
		console.log(`Debug in chart_logic.js: setChartContainerHeight called with size: ${size}. Intended height: ${height}px.`);
	} else {
		console.warn("Debug in chart_logic.js: Chart container not found for setting height.");
	}
}


// --- Functions for Custom Scrollbar Handle Dragging (Pan Bar) ---
function onMouseMovePanHandle(e) { // Renamed
	if (!isDraggingPanHandle || !myChart || !myChart.pan || !panScrollbarTrack || !panScrollbarHandle) return;

	const deltaX = e.clientX - startPanHandleX;
	//console.log(`Debug: onMouseMovePanHandle - deltaX: ${deltaX}, isDraggingPanHandle: ${isDraggingPanHandle}`); // Log deltaX

	// Calculate the new requested left position of the handle
	const requestedHandleLeft = startPanHandleLeft + deltaX;

	// Clamp the handle position within the track boundaries
	const trackWidth = panScrollbarTrack.offsetWidth;
	const handleWidth = panScrollbarHandle.offsetWidth;
	const maxHandleLeft = trackWidth - handleWidth;
	const clampedHandleLeft = Math.max(0, Math.min(requestedHandleLeft, maxHandleLeft));

// --- CALCULATE DESIRED CHART PAN BASED ON CLAMPED HANDLE POSITION ---

    const xScale = myChart.scales['x'];
    // Ensure X scale exists and original limits are defined (they should be global)
    if (!xScale || originalXScaleMin === undefined || originalXScaleMax === undefined) {
        console.warn("Debug: onMouseMovePanHandle skipped - X scale or original limits not available.");
        return;
    }

    const fullRange = originalXScaleMax - originalXScaleMin;
    const visibleRange = xScale.max - xScale.min;

    // Ensure the panable data range is valid
    const panableDataRange = fullRange - visibleRange;
    if (panableDataRange <= 0 || trackWidth - handleWidth <= 0) {
         // If chart is fully zoomed out or handle fills track, no panning is possible via handle drag
         // console.log("Debug: Chart is fully zoomed out or handle fills track, pan via handle skipped.");
         // We still update start positions to avoid jump when panning becomes possible
         startPanHandleX = e.clientX; // Update starting mouse position
         startPanHandleLeft = clampedHandleLeft; // Update starting handle left position
         return;
    }


    // Calculate the ratio of the handle's position within its travel range (0 to 1)
    const handlePositionRatio = clampedHandleLeft / (trackWidth - handleWidth);

    // Map this ratio to the chart's panable data range to find the desired new minimum value
    // The desired new min value should be the original min plus the handle's ratio of the panable data range
    const desiredXScaleMin = originalXScaleMin + handlePositionRatio * panableDataRange;

    // Calculate the pan delta needed to move the chart to the desired new min value
    // If desiredXScaleMin is greater than current xScale.min, we need to pan left (negative delta for myChart.pan)
    const panDelta = xScale.min - desiredXScaleMin; // Current min minus desired min

    // console.log(`Debug: onMouseMovePanHandle - clampedHandleLeft: ${clampedHandleLeft.toFixed(2)}, handlePositionRatio: ${handlePositionRatio.toFixed(2)}, desiredXScaleMin: ${desiredXScaleMin.toFixed(2)}, currentXScaleMin: ${xScale.min.toFixed(2)}, panDelta: ${panDelta.toFixed(2)}`); // Keep commented unless debugging pan calculation


    // Call myChart.pan() with the calculated data unit delta
    // myChart.pan({ x: panDelta, y: 0 }, undefined, 'default'); // This directly sets the center based on the delta

    // Alternatively, we can use myChart.zoom({min, max}) or update the scales directly,
    // but pan() is designed for delta movements. Let's ensure panDelta is correctly used.
    // The pan function moves the chart BY the delta.
    // If you want the chart's min to BE desiredXScaleMin, you need to calculate the required pan delta.
    // The current min is xScale.min. The target min is desiredXScaleMin.
    // A positive pan delta moves the chart to the right (showing earlier data).
    // A negative pan delta moves the chart to the left (showing later data).
    // To move the chart from xScale.min to desiredXScaleMin, the required pan delta is xScale.min - desiredXScaleMin.

     myChart.pan({ x: panDelta, y: 0 }, undefined, 'default'); // <--- Use the calculated panDelta

    // Update the starting position for the next mousemove event
    startPanHandleX = e.clientX; // Update starting mouse position
    startPanHandleLeft = clampedHandleLeft; // Update starting handle left position based on the clamped visual position

    // Prevent default browser drag behavior (might already be prevented by mousedown, but good to be sure)
    e.preventDefault();
    // e.stopPropagation(); // May not be needed if listeners are on document
}


function onMouseUpPanHandle() { // Renamed
    console.log("Debug: mouseup for pan scrollbar handle detected.");
    isDraggingPanHandle = false;
    document.removeEventListener('mousemove', onMouseMovePanHandle);
    document.removeEventListener('mouseup', onMouseUpPanHandle);

    // Ensure the handle position is finalized after drag (updateScrollbarHandle will be called by onPanComplete)
    // updateScrollbarHandle(); // This updates the pan handle - Remove this line, onPanComplete will call it
    // Fix the ReferenceError in this log by removing the reference to chartPanDeltaX
    // console.log(`Debug: onMouseMovePanHandle - Calculated chartPanDeltaX: ${chartPanDeltaX}`); // <--- REMOVE OR FIX THIS LINE
    console.log("Debug: Pan handle drag ended."); // <--- Replace with a safe log
}


// --- Functions for Custom Scrollbar Handle Dragging (Zoom Bar) ---
function onMouseMoveZoomHandle(e) {
	// Check if dragging is enabled and chart/elements exist
	if (!isDraggingZoomHandle || !myChart || !myChart.zoom || !zoomScrollbarTrack || !zoomScrollbarHandle) {
		// console.log("Debug: onMouseMoveZoomHandle skipped due to missing elements or not dragging."); // Optional: uncomment for debugging why it's not running
		return;
	}

	// Calculate the change in mouse position since the last movement
	const deltaY = e.clientY - startZoomHandleY;

	// --- Debug Log: Show the vertical drag delta ---
	console.log(`Debug: onMouseMoveZoomHandle - deltaY: ${deltaY}, isDraggingZoomHandle: ${isDraggingZoomHandle}`);


	// Calculate the new requested top position of the handle based on mouse movement
	const requestedHandleTop = startZoomHandleTop + deltaY;

	// Clamp the handle position within the track boundaries to prevent it from going outside
	const trackHeight = zoomScrollbarTrack.offsetHeight;
	const handleHeight = zoomScrollbarHandle.offsetHeight;
	const maxHandleTop = trackHeight - handleHeight;
	const clampedHandleTop = Math.max(0, Math.min(requestedHandleTop, maxHandleTop));

	// --- Calculate the zoom factor based on the vertical drag delta ---
	// Dragging down (positive deltaY) should generally zoom OUT (factor < 1)
	// Dragging up (negative deltaY) should generally zoom IN (factor > 1)
	const zoomFactorPerPixel = 0.005; // Calibration value - adjust this to control zoom sensitivity
	const intuitiveZoomFactor = 1 + (-deltaY * zoomFactorPerPixel); // Invert deltaY for intuitive direction

	// --- Debug Log: Show the calculated zoom factor BEFORE clamping ---
	console.log(`Debug: onMouseMoveZoomHandle - intuitiveZoomFactor (before clamping): ${intuitiveZoomFactor.toFixed(4)}`);


	// --- Clamp the intuitive zoom factor within defined limits ---
	// This prevents excessive zoom in or zooming out beyond the original range
	const yScale = myChart.scales['y']; // Get the Y scale

	// Ensure Y scale and original limits are available before clamping
	if (yScale && originalYScaleMin !== undefined && originalYScaleMax !== undefined && (originalYScaleMax - originalYScaleMin) > 0) {

		const minVisibleRangeFraction = 0.05; // Don't allow zooming in so much that less than 5% of data is visible
		const maxZoomInFactor = (originalYScaleMax - originalYScaleMin) / ((originalYScaleMax - originalYScaleMin) * minVisibleRangeFraction); // How many times can we zoom in relative to original?

		const maxZoomOutFactor = 0.5; // Prevent zooming out beyond the original range (factor of 1)

		// Apply clamping: factor must be at least maxZoomOutFactor (1) and at most maxZoomInFactor
		const clampedIntuitiveZoomFactor = Math.max(maxZoomOutFactor, Math.min(intuitiveZoomFactor, maxZoomInFactor));

		// --- Debug Log: Show the calculated zoom factor AFTER clamping ---
		console.log(`Debug: onMouseMoveZoomHandle - clampedIntuitiveZoomFactor (applied to chart): ${clampedIntuitiveZoomFactor.toFixed(4)}`);

		// --- Apply the clamped intuitive zoom factor to the chart's Y axis ---
		// We need a point to zoom around, let's use the center of the current chart area
		const chartAreaCenterY = (myChart.chartArea.top + myChart.chartArea.bottom) / 2;
		const chartAreaCenterX = (myChart.chartArea.left + myChart.chartArea.right) / 2; // Need an X reference point too


		// Apply the zoom factor around the center point
		// NOTE: Chart.js zoom() method zooms IN by the factor.
		// If factor > 1, it zooms in. If factor < 1, it zooms out.
		myChart.zoom(clampedIntuitiveZoomFactor, { x: chartAreaCenterX, y: chartAreaCenterY });


	} else {
		console.warn("Debug: Y scale or original scale limits not found for zoom calculation/clamping.");

	}


	// Update the starting position for the next mousemove event
	startZoomHandleY = e.clientY;
	// Update start position for next delta calculation based on clamped position
	startZoomHandleTop = clampedHandleTop; // Use clamped position for next start

}
// --- End Functions for Custom Scrollbar Handle Dragging (Zoom Bar) ---


// --- Function to handle mouseup for Custom Scrollbar Handle Dragging (Zoom Bar) ---
function onMouseUpZoomHandle() { // Added for zoom bar
	console.log("Debug: mouseup for zoom scrollbar handle detected.");
	isDraggingZoomHandle = false;
	document.removeEventListener('mousemove', onMouseMoveZoomHandle);
	document.removeEventListener('mouseup', onMouseUpZoomHandle);

	// Ensure the handle position is finalized after drag
	updateZoomHandle(); // This updates the zoom handle
}
// --- End Function for Custom Scrollbar Handle Dragging (Zoom Bar) ---

// --- Function to Update Custom Scrollbar Handle Position and Width (Pan Bar) ---
function updateScrollbarHandle() { // This updates the pan handle (bottom)
	// console.log("Debug: updateScrollbarHandle triggered for Pan."); // Keep commented unless debugging
	// Ensure scrollbar elements are defined
	if (!myChart || !panScrollbarTrack || !panScrollbarHandle) {
		// console.warn("Debug: updateScrollbarHandle skipped - chart, track, or handle not found.");
		return;
	}

	const xScale = myChart.scales['x']; // Assuming 'x' is your horizontal axis ID


	// Ensure original scale limits are defined
	if (xScale && originalXScaleMin !== undefined && originalXScaleMax !== undefined) {
		// Get the current visible range (min and max values on the scale)
		const minVisibleValue = xScale.min;
		const maxVisibleValue = xScale.max;

		const fullRange = originalXScaleMax - originalXScaleMin;
		const visibleRange = maxVisibleValue - minVisibleValue;

		const trackWidth = panScrollbarTrack.offsetWidth;

		// Calculate the handle width as a percentage of the track width
		// Ensure fullRange is not zero or negative to avoid division by zero
		let handleWidth = (fullRange > 0) ? (visibleRange / fullRange) * trackWidth : trackWidth;

		// Clamp handle width to avoid it being too small or too large
		const minHandleWidth = 20; // Minimum width for the handle in pixels
		handleWidth = Math.max(minHandleWidth, Math.min(handleWidth, trackWidth));


		// Calculate the handle position (left offset)
		let handleLeft = (fullRange > 0) ? ((minVisibleValue - originalXScaleMin) / fullRange) * trackWidth : 0;

		// Clamp handle position within the track boundaries
		const maxHandleLeft = trackWidth - handleWidth;
		handleLeft = Math.max(0, Math.min(handleLeft, maxHandleLeft)); // Clamp position


		// Apply the calculated styles to the handle
		panScrollbarHandle.style.width = `${handleWidth}px`;
		panScrollbarHandle.style.left = `${handleLeft}px`;

		// console.log(`Debug: Pan Handle - Visible Range: ${minVisibleValue} - ${maxVisibleValue}, Full Range: ${originalXScaleMin} - ${originalXScaleMax}, Handle Width: ${handleWidth.toFixed(2)}px, Handle Left: ${handleLeft.toFixed(2)}px`); // Keep commented unless debugging

	} else {
		// console.warn("Debug: X scale or original X scale limits not found for pan scrollbar update.");
	}
}


// --- Function to Update Custom Scrollbar Handle Position and Height (Zoom Bar) ---
function updateZoomHandle() { // Added for zoom bar (updates the side handle)
	// console.log("Debug: updateZoomHandle triggered for Zoom."); // Keep commented unless debugging
	// Ensure scrollbar elements are defined
	if (!myChart || !zoomScrollbarTrack || !zoomScrollbarHandle) {
		// console.warn("Debug: updateZoomHandle skipped - chart, track, or handle not found.");
		return;
	}

	const yScale = myChart.scales['y']; // Assuming 'y' is your vertical axis ID

	// Ensure original scale limits are defined
	if (yScale && originalYScaleMin !== undefined && originalYScaleMax !== undefined) {
		// Get the current visible range (min and max values on the scale)
		const minVisibleValue = yScale.min;
		const maxVisibleValue = yScale.max;

		const fullRange = originalYScaleMax - originalYScaleMin;
		const visibleRange = maxVisibleValue - minVisibleValue;

		const trackHeight = zoomScrollbarTrack.offsetHeight;

		// Calculate the handle height as a percentage of the track height
		// Ensure fullRange is not zero or negative
		let handleHeight = (fullRange > 0) ? (visibleRange / fullRange) * trackHeight : trackHeight;

		// Clamp handle height
		const minHandleHeight = 20; // Minimum height for the handle in pixels
		handleHeight = Math.max(minHandleHeight, Math.min(handleHeight, trackHeight));


		// A common approach: Map the CENTER of the visible range to the CENTER of the handle.
		const visibleCenterY = (minVisibleValue + maxVisibleValue) / 2;
		const fullCenterY = (originalYScaleMin + originalYScaleMax) / 2;

		// Calculate the position of the visible center relative to the full range (0 to 1)
		// Ensure fullRange is not zero
		let centerPercentage = (fullRange > 0) ? (visibleCenterY - originalYScaleMin) / fullRange : 0.5;

		// Map the center percentage to the center pixel position on the track
		const centerPixelOnTrack = centerPercentage * trackHeight;

		// The handle's top position is its center minus half its height
		let handleTop = centerPixelOnTrack - (handleHeight / 2);


		// Clamp handle position within the track boundaries
		const maxHandleTop = trackHeight - handleHeight;
		handleTop = Math.max(0, Math.min(handleTop, maxHandleTop)); // Clamp position


		// Apply the calculated styles to the handle
		zoomScrollbarHandle.style.height = `${handleHeight}px`;
		zoomScrollbarHandle.style.top = `${handleTop}px`;

		// console.log(`Debug: Zoom Handle - Visible Range Y: ${minVisibleValue} - ${maxVisibleValue}, Full Range Y: ${originalYScaleMin} - ${originalYScaleMax}, Handle Height: ${handleHeight.toFixed(2)}px, Handle Top: ${handleTop.toFixed(2)}px`); // Keep commented unless debugging

	} else {
		// console.warn("Debug: Y scale or original Y scale limits not found for zoom scrollbar update.");
	}
}

// Define the event listener functions:

function onCanvasMouseDown(e) {
    // Check if the left mouse button (0) or middle mouse button (1) was clicked
    if (e.button === 0 || e.button === 1) {
        isCanvasPanning = true;
        lastPanMouseX = e.clientX; // Store the starting X position for pan

        // Prevent default browser behavior like highlighting
        e.preventDefault();
        e.stopPropagation(); // Stop event from potentially interfering elsewhere

        console.log(`Debug: Canvas Mousedown triggered. Button: ${e.button}. Starting pan.`);

					// Add a variable to track if panning is active on the canvas
    }
}

function onCanvasMouseMove(e) {
    if (!isCanvasPanning || !myChart) return; // Only pan if the flag is set and chart exists

    // Calculate the difference in mouse position
    const deltaX = e.clientX - lastPanMouseX;
    //console.log(`Debug: Canvas Mousemove panning. deltaX: ${deltaX}`);

    // Calculate the pan amount in chart scale units based on pixel movement
    // This mapping requires calibration. A simple approach is to map pixels to a fraction of the visible range.
    const xScale = myChart.scales['x'];
    if (!xScale) return;

	console.log(`Debug: onCanvasMouseMove - mouse deltaX: ${deltaX}`);
	console.log(`Debug: onCanvasMouseMove - dataUnitsPerPixel: ${dataUnitsPerPixel}`);
	console.log(`Debug: onCanvasMouseMove - panSpeedFactor: ${panSpeedFactor}`);
	console.log(`Debug: onCanvasMouseMove - xScale.min (before pan): ${xScale.min}, xScale.max (before pan): ${xScale.max}`);

    // --- NEW PAN AMOUNT CALCULATION USING SCALE MAPPING ---
    // Get the data value at the starting pixel position
    const startValue = xScale.getValueForPixel(xScale.left + (lastPanMouseX - myChart.chartArea.left)); // Value at the start of the mouse drag relative to chart area

    // Get the data value at the current pixel position
    const currentValue = xScale.getValueForPixel(xScale.left + (e.clientX - myChart.chartArea.left)); // Value at the current mouse position relative to chart area
    const panAmount = currentValue - startValue;

    // We still need to scale this by a panSpeedFactor for overall control
    // Note: This calculation already provides a consistent FEELING per pixel
    // You might not need a separate panSpeedFactor multiplier here unless you want to globally speed up/slow down the pixel-to-data mapping sensitivity.
    // Let's remove the panSpeedFactor from here for now and rely on the scale mapping.
    // If you need to adjust global sensitivity, we can find another way or put it back.
    // const panAmount = (currentValue - startValue) * panSpeedFactor; // If you want an overall factor

    // --- DEBUG LOGS FOR NEW CALCULATION ---
    // console.log(`Debug: Pan calculation - startValue: ${startValue}, currentValue: ${currentValue}, panAmount: ${panAmount}`);
    // --- End Debug Logs ---


    // Call myChart.pan() with the calculated data unit delta
    // Note: myChart.pan({x, y}) moves the chart by the delta.
    // If you pan the mouse to the right (positive deltaX), the chart should move left (showing earlier data).
    // Moving left visually corresponds to a negative delta in myChart.pan() for a standard x-axis where values increase to the right.
    // The calculated 'panAmount' here is (currentValue - startValue). If currentValue > startValue (mouse moved right), panAmount is positive.
    // To move the chart left, we need a negative pan delta.
    // So, the pan delta for myChart.pan should be -(currentValue - startValue) or (startValue - currentValue).
    const panDeltaForPlugin = startValue - currentValue; // The difference from start to current gives the required pan delta

    // Apply the pan using the plugin's API
    // The pan() method takes a delta in scale units. For horizontal pan, we pan by {x: panAmount}.
    myChart.pan({ x: -panDeltaForPlugin, y: 0 }, undefined, 'default'); // Note the negative panAmount if deltaX > 0 moves chart left

    // Update the last mouse position for the next move event
    lastPanMouseX = e.clientX;

    // Prevent default behavior
    e.preventDefault();
    //e.stopPropagation();
}

function onCanvasMouseUp(e) {
    if (isCanvasPanning) {
        isCanvasPanning = false;
        console.log("Debug: Canvas Mouseup, ending pan.");

        // Prevent default behavior
        e.preventDefault();
        e.stopPropagation();
    }
}


// Function to create and render a Chart.js chart
function createChart(chartType, chartData, xAxisLabel = 'X-Axis', yAxisLabel = 'Y-Axis') {
    console.log(`Debug in chart_logic.js: Attempting to create chart of type: ${chartType}`);

    // Get the canvas element where Chart.js will draw
    const ctx = document.getElementById('myChart');

    // Basic check for valid canvas and data
    if (!ctx) {
        console.error("Error in chart_logic.js: Canvas element with ID 'myChart' not found for creation.");
        return null; // Exit and return null if canvas not found
    }
    if (!chartData || !chartData.labels || !chartData.datasets || chartData.datasets.length === 0) {
        console.warn("Debug in chart_logic.js: Provided chartData is invalid or empty for creation.");
        // Optionally display a message to the user indicating no data to chart for selected axes
        return null; // Return null if data is invalid
    }

    // Define chart options based on type (you can customize these further)
    let chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {}, // Initialize scales object

        plugins: { // <--- PLUGINS OBJECT
            legend: {
                display: true,
                position: 'top',
            },
            title: { display: true, text: yAxisLabel + ' over ' + xAxisLabel },

            // --- CHART.JS ZOOM PLUGIN CONFIGURATION ---
            zoom: {
                pan: {
                    enabled: false, // Keep plugin pan disabled for now (we'll use custom)
                    mode: 'x', // Pan along the X-axis only (or 'xy' or 'y')
					//speed: 0.05,
                    // limits: { // Optional: Configure limits
                    //     x: 'original', // Limit pan to the original data range
                    // },
                },
                zoom: {
                    wheel: {
                        enabled: true, // Enable zooming with mouse wheel
                        speed: 0.1, // Adjust zoom speed as needed
                        mode: 'x', // Zoom only on the Y-axis with mouse wheel (optional, default is 'xy')
                    },
                    pinch: {
                        enabled: true // Enable zooming with pinch gestures
                    },
                    mode: 'x', // Set the default mode for zoom (applies to wheel and pinch unless overridden)
                              // Set to 'xy' if you want wheel/pinch to zoom both axes
                    limits: { // Optional: Configure limits
                         y: 'original', // Limit zoom to the original data range for Y (or 'original')
                         // x: 'original', // Limit zoom to the original data range for X
                    },
                    // Optional: Disable drag-to-zoom rectangle selection if you don't want it
                    // drag: { enabled: false },
                },
                // --- Zoom Plugin Event Handlers to Update Scrollbars ---
                // These hooks are essential for updating your custom scrollbar handles
                onZoomComplete: function({chart}) {
                    // console.log("Debug: Chart zoom complete. Updating scrollbar handles."); // Keep commented unless debugging hook
                    updateScrollbarHandle(); // Update pan handle (bottom)
                    updateZoomHandle(); // Update zoom handle (side)
                },
                onPanComplete: function({chart}) {
                    // console.log("Debug: Chart pan complete. Updating scrollbar handles."); // Keep commented unless debugging hook
                    updateScrollbarHandle(); // Update pan handle (bottom)
                    updateZoomHandle(); // Update zoom handle (side)
                },
            },
            // Your tooltip configuration should also be inside 'plugins'
            tooltip: {
                callbacks: {
                    label: function(context) {
                        let label = context.dataset.label || '';
                        if (label) {
                            label += ': ';
                        }
                        let value = context.raw;
                        if (typeof value === 'number') {
                            label += value.toFixed(2);
                        } else {
                            label += value;
                        }
                        return label;
                    },
                    title: function(context) {
                        return context[0].label;
                    }
                }
            }
        },
        // Define scales outside the plugins object for bar/line charts
        // This block will be added/overwritten below based on chart type
    };

    // Customize scales based on chart type (only apply scales to bar/line charts)
    if (chartType === 'bar' || chartType === 'line') {
        chartOptions.scales = { // <--- Ensure this is assigned to chartOptions.scales
            y: {
                title: { display: true, text: yAxisLabel },
                // Calculate suggestedMax/Min based on data, ensuring numbers are filtered
                suggestedMax: chartData.datasets[0].data.filter(v => typeof v === 'number').length > 0 ? Math.max(0, ...chartData.datasets[0].data.filter(v => typeof v === 'number')) * 1.1 : 10,
                suggestedMin: chartData.datasets[0].data.filter(v => typeof v === 'number').length > 0 ? Math.min(0, ...chartData.datasets[0].data.filter(v => typeof v === 'number')) * 1.1 : 0,
                // Allow Y-axis scale to be controlled by zoom (don't limit to 'original' here)
            },
            x: {
                title: { display: true, text: xAxisLabel },
                ticks: { autoSkip: true, maxTicksLimit: 15, maxRotation: 45, minRotation: 0 }
                // Allow X-axis scale to be controlled by pan (don't limit to 'original' here)
            }
        };
    } else {
        // For chart types without standard x/y scales (like pie/doughnut), ensure scales object is still present but empty
        chartOptions.scales = {};
    }


    let ChartInstance = null; // Declare a local variable for the instance within the function

    try {
        // --- LOG CHART OPTIONS BEFORE CREATION ---
        console.log("Debug: Inside createChart, chartOptions being passed to new Chart():", chartOptions);

        // Create the chart instance using the canvas context, type, data, and options
        ChartInstance = new Chart(ctx, { // Assign to the local variable ChartInstance
            type: chartType,
            data: chartData,
            options: chartOptions // Pass the defined options object
        });

        // --- LOG THE LOCAL INSTANCE AFTER ASSIGNMENT ---
        console.log("Debug: Inside createChart, ChartInstance after assignment:", ChartInstance); // <--- Corrected log

    } catch (chartError) {
        // --- ENSURE FULL ERROR LOGGING ---
        console.error("Error creating Chart.js instance:", chartError); // Log the error message
        console.error("Error details:", chartError); // <--- Log the full error object
        ChartInstance = null; // Ensure local variable is null on error
    }

    return ChartInstance; // Return the local instance (or null)
}


// Wait for the DOM to be fully loaded before trying to render the chart
window.onload = async function() {
    console.log("Debug in chart_logic.js: Window fully loaded.");

    // --- Initial Data Fetching and Element Getting ---
    const dataElement = document.getElementById('extracted-data-json');
    const fetchUrlElement = document.getElementById('fetch-data-url');
    const csrfTokenElement = document.querySelector('[name=csrfmiddlewaretoken]');

    let initialChartData = null;
    let fetchUrl = null;
    let csrfToken = null;

    if (dataElement) {
        const jsonText = dataElement.textContent;
        console.log("Debug in chart_logic.js: Found and got text content from 'extracted-data-json' element.");
        try {
            initialChartData = JSON.parse(jsonText);
            console.log("Debug in chart_logic.js: Successfully parsed initial JSON chart data.", initialChartData);
        } catch (error) {
            console.error("Error parsing initial JSON data:", error);
        }
    } else {
        console.warn("Debug in chart_logic.js: 'extracted-data-json' element not found.");
    }

    if (fetchUrlElement && csrfTokenElement) {
        try {
            fetchUrl = JSON.parse(fetchUrlElement.textContent).fetch_data_url;
            csrfToken = csrfTokenElement.value;
            console.log("Debug in chart_logic.js: Fetch URL and CSRF token found.");
        } catch (error) {
            console.error("Error getting fetch URL or CSRF token:", error);
        }
    } else {
        console.warn("Debug in chart_logic.js: Fetch URL element or CSRF token element not found.");
    }

    // Get references to the selector elements
    const chartTypeSelector = document.getElementById('chartTypeSelector');
    const chartSizeSelector = document.getElementById('chartSizeSelector');
    const xAxisSelector = document.getElementById('xAxisSelector');
    const yAxisSelector = document.getElementById('yAxisSelector');

    console.log("Debug in chart_logic.js: chartTypeSelector element:", chartTypeSelector);
    console.log("Debug in chart_logic.js: chartSizeSelector element:", chartSizeSelector);
    console.log("Debug in chart_logic.js: xAxisSelector element:", xAxisSelector);
    console.log("Debug in chart_logic.js: yAxisSelector element:", yAxisSelector);


    // Check if initial data is available and Chart.js is loaded
    if (initialChartData && typeof Chart === 'function') {
        console.log("Debug in chart_logic.js: Initial chart data available and Chart.js library is loaded. Attempting initial chart creation.");

        // Set initial chart size based on selector
        const initialChartSize = chartSizeSelector ? chartSizeSelector.value : 'medium';
        setChartContainerHeight(initialChartSize); // Call function to set container height

        // Create the initial chart
        const initialChartType = chartTypeSelector ? chartTypeSelector.value : 'bar';
        const initialXAxisLabel = (xAxisSelector && xAxisSelector.options && xAxisSelector.selectedIndex !== -1) ? xAxisSelector.options[xAxisSelector.selectedIndex].text : 'X-Axis';
        const initialYAxisLabel = (yAxisSelector && yAxisSelector.options && yAxisSelector.selectedIndex !== -1) ? yAxisSelector.options[yAxisSelector.selectedIndex].text : 'Y-Axis';

        // --- CREATE THE CHART ONCE AND ASSIGN TO GLOBAL myChart ---
        myChart = createChart(initialChartType, initialChartData, initialXAxisLabel, initialYAxisLabel);

        // --- CHECK IF myChart WAS SUCCESSFULLY CREATED BEFORE PROCEEDING ---
        if (myChart) {
            console.log("Debug: Chart object created successfully and assigned to global myChart in window.onload.");

             // --- Store Original Scale Limits after initial render ---
             // Use a small timeout to ensure scales are initialized and chart area dimensions are calculated
            setTimeout(() => {
                const xScale = myChart.scales['x'];
                const yScale = myChart.scales['y'];

                if (xScale) {
                    originalXScaleMin = xScale.min;
                    originalXScaleMax = xScale.max;
                    console.log(`Debug: Stored original X scale limits: min=${originalXScaleMin}, max=${originalXScaleMax}`);
                } else {
                    console.warn("Debug: X scale not available to store original limits.");
                }
                if (yScale) {
                    originalYScaleMin = yScale.min;
                    originalYScaleMax = yScale.max;
                    console.log(`Debug: Stored original Y scale limits: min=${originalYScaleMin}, max=${originalYScaleMax}`);
                } else {
                    console.warn("Debug: Y scale not available to store original limits.");
                }

                 // --- CALCULATE DATA UNITS PER PIXEL FOR CONSISTENT PAN SPEED ---
                if (xScale && originalXScaleMin !== undefined && originalXScaleMax !== undefined) {
                    const initialDataRange = originalXScaleMax - originalXScaleMin;
                    const chartAreaWidth = myChart.chartArea.width; // Pixel width of the plotting area

                    // --- DEBUG LOGS FOR CALCULATION ---
                    console.log(`Debug: dataUnitsPerPixel calculation - originalXScaleMin: ${originalXScaleMin}`);
                    console.log(`Debug: dataUnitsPerPixel calculation - originalXScaleMax: ${originalXScaleMax}`);
                    console.log(`Debug: dataUnitsPerPixel calculation - initialDataRange: ${initialDataRange}`);
                    console.log(`Debug: dataUnitsPerPixel calculation - chartAreaWidth: ${chartAreaWidth}`);
                    // --- End Debug Logs ---

                    if (chartAreaWidth > 0 && initialDataRange > 0) { // Add check for initialDataRange > 0
                        dataUnitsPerPixel = initialDataRange / chartAreaWidth;
                        console.log(`Debug: Calculated dataUnitsPerPixel: ${dataUnitsPerPixel}`);
                        // You can adjust panSpeedFactor globally or here if needed
                        // panSpeedFactor = 1.5; // Example: Make pan 1.5 times faster
                    } else {
                        console.warn("Debug: Chart area width is zero or initial data range is zero, cannot calculate dataUnitsPerPixel.");
                        dataUnitsPerPixel = 0; // Ensure it's zero if calculation is not possible
                    }
                } else {
                    console.warn("Debug: X scale or original limits not available to calculate dataUnitsPerPixel.");
                    dataUnitsPerPixel = 0; // Ensure it's zero if data is missing
                }

                // --- PERFORM INITIAL SCROLLBAR UPDATES AFTER CALCULATION ---
                // Call both update functions here as onZoomComplete/onPanComplete are also used for initial render
                updateScrollbarHandle(); // Initial update for pan handle
                updateZoomHandle(); // Initial update for zoom handle


            }, 50); // Small delay to allow Chart.js render and dimension calculation

            // --- Get Custom Scrollbar Elements ---
            const panControl = document.querySelector('.custom-scrollbar-control.pan-control');
            const zoomControl = document.querySelector('.custom-scrollbar-control.zoom-control');

            // Assign to global variables
            panScrollbarTrack = panControl ? panControl.querySelector('.scrollbar-track') : null;
            panScrollbarHandle = panControl ? panControl.querySelector('.scrollbar-handle') : null;
            panScrollbarArrowLeft = panControl ? panControl.querySelector('.scrollbar-arrow.left') : null;
            panScrollbarArrowRight = panControl ? panControl.querySelector('.scrollbar-arrow.right') : null;

            zoomScrollbarTrack = zoomControl ? zoomControl.querySelector('.scrollbar-track') : null;
            zoomScrollbarHandle = zoomControl ? zoomControl.querySelector('.scrollbar-handle') : null;
            zoomScrollbarArrowUp = zoomControl ? zoomControl.querySelector('.scrollbar-arrow.up') : null;
            zoomScrollbarArrowDown = zoomControl ? zoomControl.querySelector('.scrollbar-arrow.down') : null;

            console.log("Debug: Elements found. Adding all listeners.");
             // --- Add these console logs AFTER the querySelector calls ---
            console.log("Debug: panControl element:", panControl);
            console.log("Debug: panScrollbarTrack element:", panScrollbarTrack);
            console.log("Debug: panScrollbarHandle element:", panScrollbarHandle);
            console.log("Debug: panScrollbarArrowLeft element:", panScrollbarArrowLeft);
            console.log("Debug: panScrollbarArrowRight element:", panScrollbarArrowRight);
            console.log("Debug: zoomControl element:", zoomControl); // Added zoom element logs
            console.log("Debug: zoomScrollbarTrack element:", zoomScrollbarTrack);
            console.log("Debug: zoomScrollbarHandle element:", zoomScrollbarHandle);
            console.log("Debug: zoomScrollbarArrowUp element:", zoomScrollbarArrowUp);
            console.log("Debug: zoomScrollbarArrowDown element:", zoomScrollbarArrowDown);
            console.log("Debug: myChart object:", myChart);


            // --- ATTACH CANVAS LISTENERS (MOVED INSIDE THIS BLOCK) ---
            // The check 'if (myChart)' is implicitly handled by the outer if
            console.log("Debug: Adding canvas listeners to myChart.canvas.");
            // Ensure passive: false is added for mousedown to prevent default autoscroll
            myChart.canvas.addEventListener('mousedown', onCanvasMouseDown, { passive: false });
            document.addEventListener('mousemove', onCanvasMouseMove);
            document.addEventListener('mouseup', onCanvasMouseUp);


            // --- ATTACH PAN SCROLLBAR LISTENERS ---
            if (panScrollbarHandle && panScrollbarTrack && myChart.pan) {
                console.log("Debug: Pan scrollbar listeners found. Adding drag listeners.");
                // --- Implement Drag functionality for the Pan Scrollbar Handle ---
                panScrollbarHandle.addEventListener('mousedown', (e) => {
                    console.log("Debug: mousedown on pan scrollbar handle detected.");
                    isDraggingPanHandle = true;
                    startPanHandleX = e.clientX;
                    startPanHandleLeft = panScrollbarHandle.offsetLeft; // Store initial handle left offset

                    document.addEventListener('mousemove', onMouseMovePanHandle);
                    document.addEventListener('mouseup', onMouseUpPanHandle);

                    e.preventDefault(); // Prevent default browser drag behavior
                    console.log("Debug: Prevented default behavior on pan mousedown.");
                });
                // --- Implement Click functionality for Pan Arrow Buttons (Basic Pan Steps) ---
                const panStepPixels = 50; // Define how many pixels to pan per click

                if(panScrollbarArrowLeft && myChart && myChart.pan) {
                    console.log("Debug: Pan left arrow found. Adding click listener.");
                    panScrollbarArrowLeft.addEventListener('click', () => {
                        console.log("Debug: Pan left arrow clicked.");
                        // Pan right (positive x delta pans chart left visually)
                        myChart.pan({ x: panStepPixels, y: 0 }, undefined, 'default');
                        // updateScrollbarHandle will be called by onPanComplete
                    });
                }

                if(panScrollbarArrowRight && myChart && myChart.pan) {
                    console.log("Debug: Pan right arrow found. Adding click listener.");
                    panScrollbarArrowRight.addEventListener('click', () => {
                        console.log("Debug: Pan right arrow clicked.");
                        // Pan left (negative x delta pans chart right visually)
                        myChart.pan({ x: -panStepPixels, y: 0 }, undefined, 'default');
                        // updateScrollbarHandle will be called by onPanComplete
                    });
                }

            } else {
                console.warn("Debug: Pan scrollbar elements or myChart.pan not found for script logic.");
            }

            // --- ATTACH ZOOM SCROLLBAR LISTENERS ---
            if (zoomScrollbarHandle && zoomScrollbarTrack && myChart.zoom) {
                console.log("Debug: Zoom scrollbar listeners found. Adding drag listeners.");

                // --- Implement Drag functionality for the Zoom Scrollbar Handle ---
                zoomScrollbarHandle.addEventListener('mousedown', (e) => {
                    console.log("Debug: mousedown on zoom scrollbar handle detected.");
                    isDraggingZoomHandle = true;
                    startZoomHandleY = e.clientY;
                    startZoomHandleTop = zoomScrollbarHandle.offsetTop; // Store initial handle top offset

                    document.addEventListener('mousemove', onMouseMoveZoomHandle);
                    document.addEventListener('mouseup', onMouseUpZoomHandle);

                    e.preventDefault(); // Prevent default browser drag behavior
                });

                // --- Implement Click functionality for Zoom Arrow Buttons (Basic Zoom Steps) ---
                const zoomStepFactor = 1.1; // Zoom in by 10% per click

                if (zoomScrollbarArrowUp && myChart && myChart.zoom) {
                    console.log("Debug: Zoom up arrow found. Adding click listener.");
                    zoomScrollbarArrowUp.addEventListener('click', () => {
                        console.log("Debug: Zoom up arrow clicked (Zoom In).");
                        // Zoom in around the center of the chart area
                        const chartAreaCenterX = (myChart.chartArea.left + myChart.chartArea.right) / 2;
                        const chartAreaCenterY = (myChart.chartArea.top + myChart.chartArea.bottom) / 2;
                        myChart.zoom(zoomStepFactor, { x: chartAreaCenterX, y: chartAreaCenterY });
                        // updateZoomHandle will be called by onZoomComplete
                    });
                }

                if (zoomScrollbarArrowDown && myChart && myChart.zoom) {
                    console.log("Debug: Zoom down arrow found. Adding click listener.");
                    zoomScrollbarArrowDown.addEventListener('click', () => {
                        console.log("Debug: Zoom down arrow clicked (Zoom Out).");
                        // Zoom out around the center of the chart area
                        const chartAreaCenterX = (myChart.chartArea.left + myChart.chartArea.right) / 2;
                        const chartAreaCenterY = (myChart.chartArea.top + myChart.chartArea.bottom) / 2;
                        myChart.zoom(1 / zoomStepFactor, { x: chartAreaCenterX, y: chartAreaCenterY }); // Use 1/factor to zoom out
                        // updateZoomHandle will be called by onZoomComplete
                    });
                }

            } else {
                console.warn("Debug: Zoom scrollbar elements or myChart.zoom not found for script logic.");
            }


            // --- Add event listeners for selector changes ---
            // Get references to selectors again to ensure they are not null
            const chartTypeSelector = document.getElementById('chartTypeSelector');
            const chartSizeSelector = document.getElementById('chartSizeSelector');
            const xAxisSelector = document.getElementById('xAxisSelector');
            const yAxisSelector = document.getElementById('yAxisSelector');


            if (chartTypeSelector) {
                chartTypeSelector.addEventListener('change', updateChart);
            }
            if (chartSizeSelector) {
                chartSizeSelector.addEventListener('change', updateChart);
            }
            if (xAxisSelector) {
                xAxisSelector.addEventListener('change', updateChart);
            }
            if (yAxisSelector) {
                yAxisSelector.addEventListener('change', updateChart);
            }
            // --- End Add event listeners ---


        } else {
            console.error("Debug: myChart object was NOT created successfully by createChart. Cannot proceed with listeners.");
        }

    } else {
        console.warn("Debug in chart_logic.js: No valid initial chart data available or Chart.js not loaded. Skipping chart creation and event listeners.");
    }
}; // <--- Closing brace for window.onload function


// --- Function to handle chart updates based on selected axes (Triggers AJAX) ---
// This function definition is outside the window.onload block
async function updateChart(event) {
	console.log("Debug in chart_logic.js: updateChart function triggered.");

	// Prevent default event behavior (e.g., form submission if controls are in a form)
	if (event) {
		event.preventDefault();
		console.log("Debug in chart_logic.js: Default event behavior prevented.");
	}

	// Get references to selectors again to ensure they are not null
	const chartTypeSelector = document.getElementById('chartTypeSelector');
	const chartSizeSelector = document.getElementById('chartSizeSelector');
	const xAxisSelector = document.getElementById('xAxisSelector');
	const yAxisSelector = document.getElementById('yAxisSelector');

	const selectedXAxis = xAxisSelector ? xAxisSelector.value : null;
	const selectedYAxis = yAxisSelector ? yAxisSelector.value : null;
	const currentChartType = chartTypeSelector ? chartTypeSelector.value : 'bar';
	const currentChartSize = chartSizeSelector ? chartSizeSelector.value : 'medium';

	console.log(`Debug in chart_logic.js: Selected X-Axis: ${selectedXAxis}, Selected Y-Axis: ${selectedYAxis}`);

	if (selectedXAxis && selectedYAxis) {
		console.log(`Debug in chart_logic.js: Axes selected. Fetching new data for X=<span class="math-inline">\{selectedXAxis\}, Y\=</span>{selectedYAxis}`);

		// Get fetch URL and CSRF token again if needed (though they should be available from window.onload scope)
		const fetchUrlElement = document.getElementById('fetch-data-url');
		const csrfTokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
		const fetchUrl = fetchUrlElement ? JSON.parse(fetchUrlElement.textContent).fetch_data_url : null;
		const csrfToken = csrfTokenElement ? csrfTokenElement.value : null;


		if (!fetchUrl || !csrfToken) {
			console.error("Error in updateChart: Fetch URL or CSRF token not available.");
			alert("Configuration error: Could not fetch chart update URL.");
			destroyChart();
			return;
		}


		try {
			const response = await fetch(fetchUrl, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'X-CSRFToken': csrfToken,
				},
				body: JSON.stringify({
					'xAxis': selectedXAxis,
					'yAxis': selectedYAxis,
				}),
			});

			if (!response.ok) {
				const errorDetails = await response.json();
				console.error(`Error fetching chart data: ${response.status} ${response.statusText}`, errorDetails);
				alert(`Error fetching chart data: ${errorDetails.error || 'Unknown error'}`);
				destroyChart(); // Destroy chart on fetch error
				return;
			}

			const newChartData = await response.json();

			console.log("Debug in chart_logic.js: Successfully fetched new chart data:", newChartData);

			destroyChart(); // Destroy existing chart before creating new one
			setChartContainerHeight(currentChartSize); // Set height based on size selector
			createChart(currentChartType, newChartData, selectedXAxis, selectedYAxis); // Create new chart

			// After updating the chart, ensure the scrollbar handles are updated
			// updateScrollbarHandle and updateZoomHandle are now called by onZoomComplete/onPanComplete after chart render
			// If initial update is still an issue, consider adding a small timeout here too.


	} catch (error) {
		console.error("Error during fetch operation:", error);
		alert("An error occurred while fetching chart data.");
		destroyChart(); // Destroy chart on fetch error
	}
}}
