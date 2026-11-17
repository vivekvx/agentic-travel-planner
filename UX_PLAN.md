# Travel planner UX plan

## What we learned

This is a comparative review of public travel flows and UX research, not a study with this app's users.

- [MakeMyTrip's flight flow](https://www.makemytrip.com/flights/) starts with departure city, arrival city, dates, and travelers. Sorting and filters follow search.
- [Booking.com's accommodation guidance](https://m.booking.com/articles/booking-holiday-home-tips.en-gb.html) places facilities, property type, ratings, and similar criteria in results filtering.
- [Baymard's travel UX research](https://baymard.com/research-articles/travel-site-ux-best-practices) recommends a prominent search entry point and usable filtering for travel results.
- [Baymard's search study](https://baymard.com/research-articles/travel-accommodations-booking-search) describes revealing secondary fields after the user begins the booking search.

## Problem in the first version

The form asked for route, dates, travelers, pace, rooms, hotel cost, local spending, interests, stars, amenities, total budget, notes, and API settings before showing any result. The user had to decide on optional details before seeing what the data could offer. Technical configuration was mixed into the traveler journey.

## Revised journey

1. **Search:** From, to, dates, travelers, and one action: **Plan my trip**.
2. **First plan:** Show a consultant explanation, suggested flight and hotel, budget status, and daily activities.
3. **Refine if useful:** Pace, interests, budget, hotel preferences, and then further preferences inside a second disclosure.
4. **Inspect details:** Show source data and offer JSON download without making either the main experience.

The first plan uses balanced pace, one room per two travelers, a ₹5,000 hotel ceiling per room/night, and ₹1,500 per person/day for food and local travel. These are editable assumptions, not facts about the traveler.

## Success checks

- A first plan requires only four visible inputs.
- The user can update preferences without re-entering route or dates.
- Missing flights and incomplete budgets remain visible at the point of decision.
- The core interface works without an LLM key; developer configuration is separate.
- The interface still provides the assignment's structured JSON output.
