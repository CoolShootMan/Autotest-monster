/**
 * Set-of-Mark (SOM) Labeling Script
 * Finds interactive elements and overlays a red numbered label.
 */
(function () {
    // 1. Cleanup old labels
    const oldLabels = document.querySelectorAll('.ai-som-label');
    oldLabels.forEach(el => el.remove());

    // 2. Identify active Modal/Drawer
    const activeDrawer = document.querySelector('.MuiDrawer-root, .MuiModal-root');
    const drawerTitle = activeDrawer ? (activeDrawer.querySelector('h1, h2, h3, h4, h5, h6, .MuiTypography-root')?.innerText || 'Unknown Drawer') : null;

    const elements = document.querySelectorAll('button, input, a, [role="button"], [role="link"], [role="radio"], [role="checkbox"], .MuiButtonBase-root');
    const mapping = {
        context: {
            is_drawer_open: !!activeDrawer,
            drawer_title: drawerTitle
        },
        elements: []
    };

    elements.forEach((el, index) => {
        const rect = el.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0 && rect.top >= 0 && rect.left >= 0) {
            const isInsideDrawer = activeDrawer && activeDrawer.contains(el);
            const labelId = index + 1;
            const label = document.createElement('div');
            label.className = 'ai-som-label';
            label.innerText = labelId;
            Object.assign(label.style, {
                position: 'fixed',
                top: rect.top + 'px',
                left: rect.left + 'px',
                backgroundColor: 'red',
                color: 'white',
                fontSize: '12px',
                fontWeight: 'bold',
                padding: '2px 5px',
                borderRadius: '50%',
                zIndex: '2147483647',
                pointerEvents: 'none',
                boxShadow: '0 0 5px black'
            });
            document.body.appendChild(label);

            // Tag the actual element for framework locating
            el.setAttribute('data-som-id', labelId);

            mapping.elements.push({
                id: labelId,
                role: el.getAttribute('role') || el.tagName.toLowerCase(),
                text: el.innerText || el.getAttribute('aria-label') || '',
                placeholder: el.getAttribute('placeholder') || '',
                name: el.getAttribute('name') || '',
                context: isInsideDrawer ? 'foreground_drawer' : 'background'
            });
        }
    });
    return mapping;
})();
