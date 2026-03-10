# Pear System (Autotest-Monster) AI Testing Knowledge Base

## 1. System Overview & Architecture
* **Business Model:** Pear is a hybrid social commerce platform featuring both B2C (Consumer) and B2B (Curator/Creator) functionalities.
* **Platform Type:** Mobile-first web application, heavily utilizing responsive design, bottom navigation bars, and floating action buttons (FAB).
* **UI Framework:** Material-UI (MUI). Contains complex components like Drawers (bottom sheets), Dialogs, Popovers, and overlapping z-index layers.
* **Core Domains:**
  * **Explore `/explore`:** The B2C consumer-facing feed where users discover posts, events, and shops.
  * **Events `/events`:** The B2B/Creator management portal for creating and tracking events and associated posts.
  * **Shops/Products:** Module for managing discoverable shoppable items.

## 2. Common Navigation & Layout Patterns
* **Creating Content (The FAB Pattern):** In mobile layouts (like `/events`), creating new content (Post, Event, Product) is almost ALWAYS initiated via the central `+` Floating Action Button on the bottom navigation bar. It is NOT initiated by a top-right "Create" button (which often leads to the wrong flow or is desktop-only).
* **Two-Step Creation:** Clicking the FAB usually opens a drawer/menu. You must then click the specific intent (e.g., "Create a Post", "Create an event").
* **Post-Creation Redirection:** After successfully creating a post or item, the system often redirects the user to the public face of that item (e.g., the `Explore` feed) to preview it. To continue managing the item, the test MUST explicitly navigate back to the management URL (e.g., `/events`).

## 3. UI Element Characteristics (Locator Strategies)
* **Events List (`/events`):** Events are often listed in MuiGrid or List structures. Clicking an event to "Enter" its management view requires targeting the text of the event explicitly (e.g., `role="paragraph"` and `force: true`) because the surrounding cards have overlapping hit-testing issues.
* **Entering an Event vs Context Menu:** There are two ways to manage an event from the list:
  2. Click the **"More" (three dots `...`)** menu. *CRITICAL:* If you click the "More" menu, you MUST subsequently click "View event" from the dropdown to enter the event details/management page. Do NOT click "Edit" as that leads to a settings form.
* **Tabs:** The management view for an individual event uses MUI Tabs (e.g., "Posts", "Any-day Tickets"). These must be clicked using `role='tab'`.
* **Action Menus:** Items like Posts or Events usually have a "More" menu (`...` or similar icon) that opens a Popover/Menu containing actions like "Edit", "Delete", "Share". These menu items must be targeted with `role='menuitem'`.

## 4. Known Bugs & Automation Pitfalls
* **The "Explore Loop" Trap:** If a test attempts event management actions (like editing a post) while accidentally on the `Explore` page, AI healing will often mistake the generic "Create a Post" actions for the intended specific action. ALWAYS verify the URL is `/events` before attempting management tasks.
* **Visibility Overlays:** Playwright often reports elements as "Not Visible" even when SOM (Set-of-Mark) detects them. This is usually due to transparent `MuiBackdrop` elements or complex SVG wrappers. Forcing the click (`force: true`) or targeting the precise innermost text node is required.
* **AI Healing Misdirection:** If the AI is told to "Create a Post" but the test is already past that step and trying to edit, the AI will loop and create *another* post. Context (recent execution history) is vital to tell the AI *where* it is in the lifecycle.

## 5. Standard Test Flows (Examples)
### Flow: Creating and Editing an Event Post (`testT4777` pattern)
1. **Navigate:** Open `/events`.
2. **Initiate:** Click FAB (`+`), then "Create a Post".
3. **Confirm:** Select the event ("Lury 10378 event test"), click "Select and continue", then "Confirm".
4. **RE-NAVIGATE (Critical):** The system may redirect to preview. You MUST reopen `/events` to continue management.
5. **Manage:** Click the specific event row in the list to enter its details page.
6. **Switch Context:** Click the "Posts" tab.
7. **Action:** Click the specific post card, then click "Edit" in its popup/menu.

---
*Note: This Knowledge Base is incrementally updated as new test patterns and AI healing failures are analyzed.*
