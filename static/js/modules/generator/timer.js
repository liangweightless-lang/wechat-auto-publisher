export function createTimer(labelEl) {
    let startTime = Date.now();
    let intervalId = null;

    intervalId = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        if (labelEl) labelEl.innerText = `耗时 ${elapsed}s`;
    }, 1000);

    return {
        stop() {
            if (intervalId) clearInterval(intervalId);
        }
    };
}
