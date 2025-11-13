import streamlit as st
import pandas as pd
import random
import time

# --------------------------------------------------------------
# 🎯 Lottery Low-Payout Optimizer (7-number)
# --------------------------------------------------------------
st.set_page_config(page_title="Lottery Low-Payout Optimizer", page_icon="🎯", layout="wide")
st.title("🎯 Lottery Low-Payout Optimizer (7-number)")
st.markdown("Upload your Excel file — this tool finds 7-number combos with **low payout**, "
            "and checks if total payout < total ticket price (4 PKR per ticket).")

# --------------------------------------------------------------
# ✅ Upload File
# --------------------------------------------------------------
uploaded = st.file_uploader("📂 Upload Excel or CSV file (Column A = tickets like 1,2,3,4,5,6,7)", type=["xlsx", "csv"])

if uploaded:
    # Load file
    if uploaded.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded, header=None)
    else:
        df = pd.read_csv(uploaded, header=None)

    # Clean tickets
    tickets = []
    for row in df[0].astype(str).tolist():
        parts = [p.strip() for p in row.split(",") if p.strip()]
        nums = sorted(set(int(x) for x in parts if x.isdigit()))
        if len(nums) == 7 and all(1 <= x <= 37 for x in nums):
            tickets.append(tuple(nums))

    total_tickets = len(tickets)
    total_ticket_price = total_tickets * 4  # 💰 4 PKR per ticket
    st.success(f"✅ Loaded {total_tickets} valid tickets. Total ticket cost = {total_ticket_price:,} PKR")

    # --------------------------------------------------------------
    # 🎯 Configuration
    # --------------------------------------------------------------
    PAYOUT = {0: 0, 1: 0, 2: 0, 3: 15, 4: 750, 5: 4000, 6: 10000, 7: 100000}
    min_4, max_4 = 2, 5

    num_to_tickets = {i: [] for i in range(1, 38)}
    for idx, t in enumerate(tickets):
        for x in t:
            num_to_tickets[x].append(idx)

    # --------------------------------------------------------------
    # 🔍 Core Functions
    # --------------------------------------------------------------
    def combo_to_matches(combo):
        combo_set = set(combo)
        matches = [0] * len(tickets)
        for num in combo_set:
            for ti in num_to_tickets[num]:
                matches[ti] += 1
        return matches

    def matches_to_total(matches):
        counts = [0] * 8
        total = 0
        for m in matches:
            counts[m] += 1
            total += PAYOUT.get(m, 0)
        return total, counts

    def hill_climb(start):
        combo = list(start)
        matches = combo_to_matches(combo)
        total, counts = matches_to_total(matches)
        improved = True
        while improved:
            improved = False
            cur_set = set(combo)
            for r in combo:
                for a in range(1, 38):
                    if a in cur_set:
                        continue
                    new = combo.copy()
                    new.remove(r)
                    new.append(a)
                    new.sort()
                    matches_new = combo_to_matches(new)
                    total_new, _ = matches_to_total(matches_new)
                    # ✅ Allow only if new total payout < current total
                    if total_new < total:
                        combo = new
                        matches = matches_new
                        total = total_new
                        improved = True
                        break
                if improved:
                    break
        return combo, total, matches

    # --------------------------------------------------------------
    # ▶️ Run Optimizer
    # --------------------------------------------------------------
    if st.button("🚀 Run Optimizer"):
        st.info("Searching for low-payout combinations... This may take up to 1 minute.")
        results = []
        start = time.time()

        for _ in range(300):
            combo = random.sample(range(1, 38), 7)
            combo, total, matches = hill_climb(combo)
            total, counts = matches_to_total(matches)
            # ✅ Include only if payout < total ticket price and 2–5 tickets match 4 numbers
            if total < total_ticket_price and min_4 <= counts[4] <= max_4:
                results.append((combo, total, counts))
            if time.time() - start > 60:
                break

        # ----------------------------------------------------------
        # 📊 Show Results
        # ----------------------------------------------------------
        if results:
            res = sorted(results, key=lambda x: (x[1], -x[2][4]))[:10]
            df_out = pd.DataFrame([
                {
                    "Combo": ",".join(map(str, combo)),
                    "Total Payout (PKR)": total,
                    "Tickets with 3 matches": counts[3],
                    "Tickets with 4 matches": counts[4],
                    "Tickets with 5 matches": counts[5],
                    "Tickets with 6 matches": counts[6],
                    "Tickets with 7 matches": counts[7],
                } for combo, total, counts in res
            ])
            st.subheader("🎯 Top Low-Payout Combinations (Below Ticket Cost)")
            st.dataframe(df_out, use_container_width=True)

            # ✅ Add result summary
            best = res[0]
            st.success(
                f"💡 Best combo `{','.join(map(str,best[0]))}` has total payout {best[1]:,} PKR, "
                f"which is less than total ticket cost ({total_ticket_price:,} PKR)"
            )

            # Optional download
            csv = df_out.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Results (CSV)", data=csv, file_name="low_payout_results.csv", mime="text/csv")

        else:
            st.warning(f"No combination found with total payout below ticket cost ({total_ticket_price:,} PKR).")
