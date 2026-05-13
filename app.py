import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud


# =========================
# SETUP HALAMAN
# =========================

st.set_page_config(
    page_title="Dashboard Monitoring Media DIY",
    layout="wide"
)

st.title("Dashboard Monitoring Media DIY")
st.write(
    "Dashboard monitoring isu DIY, sentimen media, dan kesesuaian pemberitaan "
    "dengan isu dokumen perencanaan pariwisata."
)


# =========================
# MASTER ISU DOKUMEN PERENCANAAN
# =========================

MASTER_ISU_PERENCANAAN = [
    "Penguatan 6A DTW",
    "Seasonality dan Promosi Pariwisata",
    "SDM Pariwisata dan Masyarakat Destinasi",
    "Daya Saing Usaha Jasa Pariwisata"
]

DESKRIPSI_ISU = {
    "Penguatan 6A DTW": (
        "Isu terkait atraksi, aksesibilitas, amenitas, layanan pendukung, "
        "aktivitas wisata, paket wisata, travel pattern, lama tinggal, "
        "dan belanja wisatawan."
    ),
    "Seasonality dan Promosi Pariwisata": (
        "Isu terkait high season, low season, libur panjang, okupansi, "
        "event tematik, promosi digital, segmentasi pasar, dan wisatawan berkualitas."
    ),
    "SDM Pariwisata dan Masyarakat Destinasi": (
        "Isu terkait kompetensi SDM, pelatihan, sertifikasi, pokdarwis, "
        "pemandu wisata, pengelola destinasi, dan masyarakat sekitar destinasi."
    ),
    "Daya Saing Usaha Jasa Pariwisata": (
        "Isu terkait standar usaha, kredibilitas, hotel, restoran, biro perjalanan, "
        "inovasi produk, pengaturan pasar, dan daya saing usaha jasa pariwisata."
    )
}


# =========================
# FUNGSI BANTUAN
# =========================

def baca_csv(nama_file):
    try:
        df = pd.read_csv(nama_file)
        df.columns = df.columns.str.lower().str.strip()

        if "tanggal_scraping" in df.columns:
            df["tanggal_scraping"] = pd.to_datetime(
                df["tanggal_scraping"],
                errors="coerce"
            )

        if "confidence_sentimen" in df.columns:
            df["confidence_sentimen"] = pd.to_numeric(
                df["confidence_sentimen"],
                errors="coerce"
            )

        if "skor_sentimen" in df.columns:
            df["skor_sentimen"] = pd.to_numeric(
                df["skor_sentimen"],
                errors="coerce"
            )

        return df

    except FileNotFoundError:
        return None


def tampilkan_metric_sentimen(df):
    total = len(df)

    if "sentimen" in df.columns:
        positif = len(df[df["sentimen"].astype(str).str.lower() == "positif"])
        negatif = len(df[df["sentimen"].astype(str).str.lower() == "negatif"])
        netral = len(df[df["sentimen"].astype(str).str.lower() == "netral"])
    else:
        positif = 0
        negatif = 0
        netral = 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Berita", total)
    col2.metric("Positif", positif)
    col3.metric("Negatif", negatif)
    col4.metric("Netral", netral)


def tampilkan_bar_chart(df, kolom, judul):
    st.write(judul)

    if kolom not in df.columns:
        st.warning(f"Kolom {kolom} belum ada.")
        return

    hitung = df[kolom].dropna().value_counts()

    if len(hitung) == 0:
        st.info("Belum ada data.")
    else:
        st.bar_chart(hitung)


def hitung_kolom_ganda(df, kolom):
    hasil = []

    if kolom not in df.columns:
        return pd.Series(dtype="int64")

    for item in df[kolom].dropna():
        daftar = str(item).split(",")

        for nilai in daftar:
            nilai = nilai.strip()

            if nilai and nilai != "Tidak terdeteksi":
                hasil.append(nilai)

    if len(hasil) == 0:
        return pd.Series(dtype="int64")

    return pd.Series(hasil).value_counts()


def tampilkan_wordcloud(df, kolom_teks="teks"):
    if kolom_teks not in df.columns:
        st.warning("Kolom teks belum ada.")
        return

    semua_teks = " ".join(df[kolom_teks].astype(str).dropna())

    if semua_teks.strip() == "":
        st.info("Teks kosong, wordcloud belum bisa dibuat.")
        return

    wordcloud = WordCloud(
        width=1000,
        height=400,
        background_color="white",
        collocations=False
    ).generate(semua_teks)

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.imshow(wordcloud, interpolation="bilinear")
    ax.axis("off")
    st.pyplot(fig)


def filter_tanggal(df, label, key):
    if "tanggal_scraping" not in df.columns:
        return df

    if df["tanggal_scraping"].dropna().empty:
        return df

    tanggal_min = df["tanggal_scraping"].min().date()
    tanggal_max = df["tanggal_scraping"].max().date()

    rentang = st.date_input(
        label,
        value=(tanggal_min, tanggal_max),
        key=key
    )

    if isinstance(rentang, tuple) and len(rentang) == 2:
        mulai = pd.to_datetime(rentang[0])
        selesai = pd.to_datetime(rentang[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

        df = df[
            (df["tanggal_scraping"] >= mulai) &
            (df["tanggal_scraping"] <= selesai)
        ]

    return df


def filter_multiselect(df, kolom, label, key):
    if kolom not in df.columns:
        return df

    pilihan = sorted(df[kolom].dropna().unique())

    if len(pilihan) == 0:
        return df

    pilih = st.multiselect(
        label,
        pilihan,
        default=pilihan,
        key=key
    )

    if len(pilih) > 0:
        df = df[df[kolom].isin(pilih)]

    return df


def filter_pencarian_teks(df, label, key):
    kata_cari = st.text_input(label, key=key)

    if kata_cari and "teks" in df.columns:
        df = df[
            df["teks"].astype(str).str.contains(
                kata_cari,
                case=False,
                na=False
            )
        ]

    return df


def buat_ringkasan_isu_perencanaan(df):
    rows = []

    total_data = len(df)

    for isu in MASTER_ISU_PERENCANAAN:
        if "isu_perencanaan_pariwisata" in df.columns:
            df_isu = df[df["isu_perencanaan_pariwisata"] == isu]
        else:
            df_isu = pd.DataFrame()

        jumlah = len(df_isu)

        if total_data > 0:
            persentase = round((jumlah / total_data) * 100, 2)
        else:
            persentase = 0

        if "sentimen" in df_isu.columns:
            positif = len(df_isu[df_isu["sentimen"].astype(str).str.lower() == "positif"])
            negatif = len(df_isu[df_isu["sentimen"].astype(str).str.lower() == "negatif"])
            netral = len(df_isu[df_isu["sentimen"].astype(str).str.lower() == "netral"])
        else:
            positif = 0
            negatif = 0
            netral = 0

        if "confidence_sentimen" in df_isu.columns and len(df_isu) > 0:
            rata_confidence = round(df_isu["confidence_sentimen"].mean(), 3)
        else:
            rata_confidence = None

        if jumlah >= 10:
            status = "Kuat muncul di media"
        elif jumlah >= 4:
            status = "Cukup muncul di media"
        elif jumlah >= 1:
            status = "Lemah muncul di media"
        else:
            status = "Belum muncul di media"

        rows.append({
            "isu_dokumen_perencanaan": isu,
            "jumlah_berita": jumlah,
            "persentase_dari_berita_pariwisata": persentase,
            "positif": positif,
            "netral": netral,
            "negatif": negatif,
            "rata_confidence_sentimen": rata_confidence,
            "status_sinyal_media": status,
            "deskripsi": DESKRIPSI_ISU.get(isu, "")
        })

    return pd.DataFrame(rows)


def buat_insight_kesesuaian(df, ringkasan):
    if len(df) == 0:
        return "Belum ada data pariwisata yang bisa dianalisis."

    insight = []

    if len(ringkasan) > 0:
        ringkasan_urut = ringkasan.sort_values(
            by="jumlah_berita",
            ascending=False
        )

        isu_utama = ringkasan_urut.iloc[0]["isu_dokumen_perencanaan"]
        jumlah_utama = ringkasan_urut.iloc[0]["jumlah_berita"]

        insight.append(
            f"Isu dokumen perencanaan yang paling banyak muncul di media adalah "
            f"**{isu_utama}** dengan jumlah **{jumlah_utama} berita**."
        )

        isu_belum_muncul = ringkasan[
            ringkasan["jumlah_berita"] == 0
        ]["isu_dokumen_perencanaan"].tolist()

        if len(isu_belum_muncul) > 0:
            daftar_isu = ", ".join(isu_belum_muncul)

            insight.append(
                f"Terdapat isu dokumen perencanaan yang **belum banyak muncul dalam pemberitaan**, "
                f"yaitu: **{daftar_isu}**. Ini bisa berarti isu tersebut lebih bersifat internal/programatik, "
                f"atau belum menjadi sorotan media."
            )

    if "subisu_pariwisata" in df.columns:
        subisu_count = hitung_kolom_ganda(df, "subisu_pariwisata")

        if len(subisu_count) > 0:
            subisu_utama = subisu_count.index[0]
            jumlah_subisu = subisu_count.iloc[0]

            insight.append(
                f"Subisu yang paling sering muncul adalah **{subisu_utama}** "
                f"dengan jumlah kemunculan **{jumlah_subisu} kali**."
            )

    if "sentimen" in df.columns and "isu_perencanaan_pariwisata" in df.columns:
        df_negatif = df[df["sentimen"].astype(str).str.lower() == "negatif"]

        if len(df_negatif) > 0:
            negatif_per_isu = df_negatif["isu_perencanaan_pariwisata"].value_counts()

            if len(negatif_per_isu) > 0:
                isu_negatif_utama = negatif_per_isu.index[0]
                jumlah_negatif = negatif_per_isu.iloc[0]

                insight.append(
                    f"Isu dengan pemberitaan negatif paling banyak adalah "
                    f"**{isu_negatif_utama}** dengan jumlah **{jumlah_negatif} berita negatif**."
                )

    if "lokasi_diy" in df.columns:
        lokasi_count = hitung_kolom_ganda(df, "lokasi_diy")

        if len(lokasi_count) > 0:
            lokasi_utama = lokasi_count.index[0]
            jumlah_lokasi = lokasi_count.iloc[0]

            insight.append(
                f"Lokasi yang paling sering muncul dalam pemberitaan terkait isu perencanaan adalah "
                f"**{lokasi_utama}** dengan jumlah kemunculan **{jumlah_lokasi} kali**."
            )

    if "confidence_sentimen" in df.columns and "sentimen" in df.columns:
        df_negatif_yakin = df[
            (df["sentimen"].astype(str).str.lower() == "negatif") &
            (df["confidence_sentimen"] >= 0.8)
        ]

        if len(df_negatif_yakin) > 0:
            insight.append(
                f"Terdapat **{len(df_negatif_yakin)} berita negatif dengan confidence sentimen tinggi**. "
                f"Berita ini dapat diprioritaskan sebagai sinyal isu yang perlu diperhatikan."
            )

    if len(insight) == 0:
        return "Belum ditemukan pola insight yang cukup kuat dari data saat ini."

    return "\n\n".join(insight)


# =========================
# BACA DATA
# =========================

df_umum = baca_csv("hasil_analisis_diy.csv")
df_pariwisata = baca_csv("hasil_analisis_pariwisata_diy.csv")

if df_umum is None:
    st.error("File hasil_analisis_diy.csv belum ditemukan. Jalankan analisis_diy_ml.py dulu ya.")
    st.stop()

if df_pariwisata is None:
    st.warning("File hasil_analisis_pariwisata_diy.csv belum ditemukan.")
    df_pariwisata = pd.DataFrame()


# =========================
# TAB DASHBOARD
# =========================

tab_umum, tab_pariwisata, tab_perencanaan = st.tabs([
    "Dashboard Umum DIY",
    "Dashboard Pariwisata DIY",
    "Kesesuaian Isu Perencanaan"
])


# =========================
# TAB 1: DASHBOARD UMUM DIY
# =========================

with tab_umum:
    st.header("Dashboard Umum DIY")

    if len(df_umum) == 0:
        st.warning("Data umum DIY masih kosong.")
    else:
        with st.expander("Filter Data Umum DIY", expanded=True):
            df_filter = df_umum.copy()

            df_filter = filter_tanggal(
                df_filter,
                "Rentang tanggal scraping umum",
                "tanggal_umum"
            )

            df_filter = filter_multiselect(
                df_filter,
                "sentimen",
                "Pilih sentimen",
                "sentimen_umum"
            )

            df_filter = filter_multiselect(
                df_filter,
                "topik",
                "Pilih topik",
                "topik_umum"
            )

            df_filter = filter_multiselect(
                df_filter,
                "urgensi",
                "Pilih urgensi",
                "urgensi_umum"
            )

            df_filter = filter_pencarian_teks(
                df_filter,
                "Cari kata kunci berita umum DIY",
                "cari_umum"
            )

        st.subheader("Ringkasan Berita DIY")
        tampilkan_metric_sentimen(df_filter)

        st.subheader("Distribusi Analisis Umum DIY")

        col1, col2, col3 = st.columns(3)

        with col1:
            tampilkan_bar_chart(df_filter, "sentimen", "Sentimen")

        with col2:
            tampilkan_bar_chart(df_filter, "topik", "Topik")

        with col3:
            tampilkan_bar_chart(df_filter, "urgensi", "Urgensi")

        st.subheader("Lokasi DIY yang Sering Muncul")

        lokasi_count = hitung_kolom_ganda(df_filter, "lokasi_diy")

        if len(lokasi_count) > 0:
            st.bar_chart(lokasi_count)
        else:
            st.info("Belum ada lokasi DIY yang terdeteksi.")

        st.subheader("Wordcloud Berita DIY")
        tampilkan_wordcloud(df_filter)

        st.subheader("Tabel Semua Data Umum DIY")

        kolom_tampil_umum = [
            kolom for kolom in [
                "tanggal", "sumber", "judul",
                "sentimen", "confidence_sentimen", "topik", "lokasi_diy",
                "urgensi", "kata_kunci", "link"
            ]
            if kolom in df_filter.columns
        ]

        st.dataframe(
            df_filter[kolom_tampil_umum],
            use_container_width=True
        )


# =========================
# TAB 2: DASHBOARD PARIWISATA DIY
# =========================

with tab_pariwisata:
    st.header("Dashboard Pariwisata DIY")

    if len(df_pariwisata) == 0:
        st.warning("Data pariwisata DIY masih kosong.")
    else:
        with st.expander("Filter Data Pariwisata DIY", expanded=True):
            df_pariwisata_filter = df_pariwisata.copy()

            df_pariwisata_filter = filter_tanggal(
                df_pariwisata_filter,
                "Rentang tanggal scraping pariwisata",
                "tanggal_pariwisata"
            )

            df_pariwisata_filter = filter_multiselect(
                df_pariwisata_filter,
                "sentimen",
                "Pilih sentimen pariwisata",
                "sentimen_pariwisata"
            )

            df_pariwisata_filter = filter_multiselect(
                df_pariwisata_filter,
                "isu_perencanaan_pariwisata",
                "Pilih isu perencanaan pariwisata",
                "isu_pariwisata"
            )

            df_pariwisata_filter = filter_multiselect(
                df_pariwisata_filter,
                "topik",
                "Pilih topik umum",
                "topik_pariwisata"
            )

            if "confidence_sentimen" in df_pariwisata_filter.columns:
                minimal_confidence = st.slider(
                    "Minimal confidence sentimen",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.0,
                    step=0.05,
                    key="confidence_pariwisata"
                )

                df_pariwisata_filter = df_pariwisata_filter[
                    df_pariwisata_filter["confidence_sentimen"] >= minimal_confidence
                ]

            df_pariwisata_filter = filter_pencarian_teks(
                df_pariwisata_filter,
                "Cari kata kunci berita pariwisata",
                "cari_pariwisata"
            )

        st.subheader("Ringkasan Berita Pariwisata DIY")
        tampilkan_metric_sentimen(df_pariwisata_filter)

        st.subheader("Distribusi Isu Pariwisata")

        col1, col2 = st.columns(2)

        with col1:
            tampilkan_bar_chart(
                df_pariwisata_filter,
                "isu_perencanaan_pariwisata",
                "Isu Perencanaan Pariwisata"
            )

        with col2:
            tampilkan_bar_chart(
                df_pariwisata_filter,
                "sentimen",
                "Sentimen Pariwisata"
            )

        st.subheader("Subisu Pariwisata")

        subisu_count = hitung_kolom_ganda(
            df_pariwisata_filter,
            "subisu_pariwisata"
        )

        if len(subisu_count) > 0:
            st.bar_chart(subisu_count)
        else:
            st.info("Belum ada subisu pariwisata yang terdeteksi.")

        st.subheader("Lokasi Pariwisata DIY yang Sering Muncul")

        lokasi_pariwisata_count = hitung_kolom_ganda(
            df_pariwisata_filter,
            "lokasi_diy"
        )

        if len(lokasi_pariwisata_count) > 0:
            st.bar_chart(lokasi_pariwisata_count)
        else:
            st.info("Belum ada lokasi pariwisata yang terdeteksi.")

        st.subheader("Wordcloud Berita Pariwisata DIY")
        tampilkan_wordcloud(df_pariwisata_filter)

        st.subheader("Tabel Lengkap Pariwisata DIY")

        kolom_tampil_pariwisata = [
            kolom for kolom in [
                "tanggal", "sumber", "judul",
                "sentimen", "confidence_sentimen",
                "isu_perencanaan_pariwisata",
                "subisu_pariwisata", "keyword_isu_pariwisata",
                "lokasi_diy", "urgensi", "kata_kunci", "link"
            ]
            if kolom in df_pariwisata_filter.columns
        ]

        st.dataframe(
            df_pariwisata_filter[kolom_tampil_pariwisata],
            use_container_width=True
        )


# =========================
# TAB 3: KESESUAIAN ISU PERENCANAAN
# =========================

with tab_perencanaan:
    st.header("Kesesuaian Pemberitaan dengan Isu Dokumen Perencanaan")

    st.write(
        "Bagian ini digunakan untuk melihat apakah isu yang sudah masuk dalam dokumen "
        "perencanaan pariwisata juga muncul dalam pemberitaan media online."
    )

    if len(df_pariwisata) == 0:
        st.warning("Data pariwisata DIY masih kosong.")
    else:
        with st.expander("Filter Analisis Isu Perencanaan", expanded=True):
            df_perencanaan = df_pariwisata.copy()

            df_perencanaan = filter_tanggal(
                df_perencanaan,
                "Rentang tanggal scraping untuk isu perencanaan",
                "tanggal_perencanaan"
            )

            df_perencanaan = filter_multiselect(
                df_perencanaan,
                "sentimen",
                "Pilih sentimen",
                "sentimen_perencanaan"
            )

            df_perencanaan = filter_multiselect(
                df_perencanaan,
                "isu_perencanaan_pariwisata",
                "Pilih isu dokumen perencanaan",
                "isu_perencanaan"
            )

            if "confidence_sentimen" in df_perencanaan.columns:
                minimal_confidence_perencanaan = st.slider(
                    "Minimal confidence sentimen",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.0,
                    step=0.05,
                    key="confidence_perencanaan"
                )

                df_perencanaan = df_perencanaan[
                    df_perencanaan["confidence_sentimen"] >= minimal_confidence_perencanaan
                ]

            df_perencanaan = filter_pencarian_teks(
                df_perencanaan,
                "Cari kata kunci dalam berita isu perencanaan",
                "cari_perencanaan"
            )

        st.subheader("Ringkasan Media Signal terhadap Isu Dokumen Perencanaan")

        ringkasan_isu = buat_ringkasan_isu_perencanaan(df_perencanaan)

        col1, col2, col3 = st.columns(3)

        total_berita_perencanaan = len(df_perencanaan)
        jumlah_isu_muncul = len(
            ringkasan_isu[ringkasan_isu["jumlah_berita"] > 0]
        )
        jumlah_isu_belum_muncul = len(
            ringkasan_isu[ringkasan_isu["jumlah_berita"] == 0]
        )

        col1.metric("Total Berita Terkait Isu", total_berita_perencanaan)
        col2.metric("Isu Muncul di Media", jumlah_isu_muncul)
        col3.metric("Isu Belum Muncul", jumlah_isu_belum_muncul)

        st.subheader("Insight Otomatis")

        insight = buat_insight_kesesuaian(df_perencanaan, ringkasan_isu)
        st.info(insight)

        st.subheader("Ranking Isu Dokumen Perencanaan yang Muncul di Media")

        ranking_isu = ringkasan_isu.set_index("isu_dokumen_perencanaan")["jumlah_berita"]

        if len(ranking_isu) > 0:
            st.bar_chart(ranking_isu)

        st.subheader("Tabel Ringkasan Isu Dokumen Perencanaan")

        st.dataframe(
            ringkasan_isu[
                [
                    "isu_dokumen_perencanaan",
                    "jumlah_berita",
                    "persentase_dari_berita_pariwisata",
                    "positif",
                    "netral",
                    "negatif",
                    "rata_confidence_sentimen",
                    "status_sinyal_media",
                    "deskripsi"
                ]
            ],
            use_container_width=True
        )

        st.subheader("Sentimen per Isu Dokumen Perencanaan")

        if (
            "isu_perencanaan_pariwisata" in df_perencanaan.columns
            and "sentimen" in df_perencanaan.columns
            and len(df_perencanaan) > 0
        ):
            tabel_sentimen_isu = pd.crosstab(
                df_perencanaan["isu_perencanaan_pariwisata"],
                df_perencanaan["sentimen"]
            )

            st.bar_chart(tabel_sentimen_isu)

            st.dataframe(
                tabel_sentimen_isu,
                use_container_width=True
            )
        else:
            st.info("Belum ada data sentimen per isu.")

        st.subheader("Subisu yang Paling Sering Muncul")

        subisu_perencanaan_count = hitung_kolom_ganda(
            df_perencanaan,
            "subisu_pariwisata"
        )

        if len(subisu_perencanaan_count) > 0:
            st.bar_chart(subisu_perencanaan_count)
            st.dataframe(
                subisu_perencanaan_count.reset_index().rename(
                    columns={
                        "index": "subisu",
                        0: "jumlah"
                    }
                ),
                use_container_width=True
            )
        else:
            st.info("Belum ada subisu yang terdeteksi.")

        st.subheader("Artikel Pendukung Isu Dokumen Perencanaan")

        if "isu_perencanaan_pariwisata" in df_perencanaan.columns:
            pilihan_isu_bukti = st.selectbox(
                "Pilih isu untuk melihat artikel pendukung",
                MASTER_ISU_PERENCANAAN,
                key="pilih_isu_bukti"
            )

            artikel_bukti = df_perencanaan[
                df_perencanaan["isu_perencanaan_pariwisata"] == pilihan_isu_bukti
            ].copy()

            if "confidence_sentimen" in artikel_bukti.columns:
                artikel_bukti = artikel_bukti.sort_values(
                    by="confidence_sentimen",
                    ascending=False
                )

            if len(artikel_bukti) == 0:
                st.info("Belum ada artikel pendukung untuk isu ini pada data yang sedang difilter.")
            else:
                kolom_bukti = [
                    kolom for kolom in [
                        "tanggal",  "sumber", "judul",
                        "sentimen", "confidence_sentimen",
                        "isu_perencanaan_pariwisata",
                        "subisu_pariwisata",
                        "keyword_isu_pariwisata",
                        "lokasi_diy",
                        "kata_kunci",
                        "link"
                    ]
                    if kolom in artikel_bukti.columns
                ]

                st.dataframe(
                    artikel_bukti[kolom_bukti],
                    use_container_width=True
                )

        st.subheader("Artikel Negatif Confidence Tinggi")

        if "sentimen" in df_perencanaan.columns and "confidence_sentimen" in df_perencanaan.columns:
            artikel_negatif_yakin = df_perencanaan[
                (df_perencanaan["sentimen"].astype(str).str.lower() == "negatif") &
                (df_perencanaan["confidence_sentimen"] >= 0.8)
            ].copy()

            if len(artikel_negatif_yakin) > 0:
                artikel_negatif_yakin = artikel_negatif_yakin.sort_values(
                    by="confidence_sentimen",
                    ascending=False
                )

                kolom_negatif = [
                    kolom for kolom in [
                        "tanggal",  "sumber", "judul",
                        "sentimen", "confidence_sentimen",
                        "isu_perencanaan_pariwisata",
                        "subisu_pariwisata",
                        "lokasi_diy",
                        "link"
                    ]
                    if kolom in artikel_negatif_yakin.columns
                ]

                st.dataframe(
                    artikel_negatif_yakin[kolom_negatif],
                    use_container_width=True
                )
            else:
                st.info("Belum ada artikel negatif dengan confidence tinggi.")
        else:
            st.info("Kolom sentimen atau confidence_sentimen belum tersedia.")

        st.subheader("Download Ringkasan Isu Perencanaan")

        csv_ringkasan = ringkasan_isu.to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            label="Download ringkasan isu perencanaan",
            data=csv_ringkasan,
            file_name="ringkasan_isu_perencanaan_pariwisata.csv",
            mime="text/csv"
        )
