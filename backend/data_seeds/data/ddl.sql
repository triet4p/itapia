-- public.exchanges definition

-- Drop table

-- DROP TABLE public.exchanges;

CREATE TABLE public.exchanges ( exchange_code varchar(15) NOT NULL, exchange_name varchar(300) NULL, currency varchar(7) NOT NULL, timezone varchar(60) NOT NULL, country varchar(50) NOT NULL, open_time time NOT NULL, close_time time NOT NULL, CONSTRAINT exchanges_pkey PRIMARY KEY (exchange_code));

-- public.sectors definition

-- Drop table

-- DROP TABLE public.sectors;

CREATE TABLE public.sectors ( sector_code varchar(7) NOT NULL, sector_name varchar(50) NULL, CONSTRAINT sectors_pkey PRIMARY KEY (sector_code));

-- public.tickers definition

-- Drop table

-- DROP TABLE public.tickers;

CREATE TABLE public.tickers ( ticker_sym varchar(10) NOT NULL, company_name varchar(255) NULL, exchange_code varchar(15) NOT NULL, sector_code varchar(7) NOT NULL, is_active bool DEFAULT true NULL, CONSTRAINT tickers_pkey PRIMARY KEY (ticker_sym), CONSTRAINT tickers_exchange_code_fkey FOREIGN KEY (exchange_code) REFERENCES public.exchanges(exchange_code), CONSTRAINT tickers_sector_code_fkey FOREIGN KEY (sector_code) REFERENCES public.sectors(sector_code));


-- public.evo_rules definition

-- Drop table

-- DROP TABLE public.evo_rules;

CREATE TABLE public.evo_rules ( rule_id varchar(255) NOT NULL, "name" varchar(255) NOT NULL, description text NULL, purpose varchar(30) NULL, rule_status varchar(30) NULL, root jsonb NOT NULL, created_at timestamptz DEFAULT now() NOT NULL, updated_at timestamptz DEFAULT now() NOT NULL, evo_run_id varchar(255) NOT NULL, metrics jsonb NULL, CONSTRAINT evo_rules_pkey PRIMARY KEY (rule_id));


-- public.evo_runs definition

-- Drop table

-- DROP TABLE public.evo_runs;

CREATE TABLE public.evo_runs ( run_id varchar(255) NOT NULL, status varchar(30) NOT NULL, config jsonb NULL, fallback_state bytea NULL, algorithm varchar(200) NOT NULL, CONSTRAINT evo_runs_pkey PRIMARY KEY (run_id));

-- public.rules definition

-- Drop table

-- DROP TABLE public.rules;

CREATE TABLE public.rules ( rule_id varchar(255) NOT NULL, "name" varchar(255) NOT NULL, description text NULL, purpose varchar(30) NULL, root jsonb NOT NULL, created_at timestamptz DEFAULT now() NOT NULL, updated_at timestamptz DEFAULT now() NOT NULL, rule_status varchar(30) NULL, CONSTRAINT rules_pkey PRIMARY KEY (rule_id));


-- public.universal_news definition

-- Drop table

-- DROP TABLE public.universal_news;

CREATE TABLE public.universal_news ( news_uuid varchar(256) NOT NULL, keyword varchar(150) NOT NULL, title text NOT NULL, summary text NULL, provider varchar(150) NULL, link text NULL, publish_time timestamptz NULL, collect_time timestamptz NOT NULL, keyword_tsv tsvector NOT NULL, title_hash varchar(100) NOT NULL, news_prior int4 NOT NULL, CONSTRAINT universal_news_pkey PRIMARY KEY (news_uuid), CONSTRAINT universal_news_unique UNIQUE (title_hash));
CREATE INDEX keyword_tsv_idx ON public.universal_news USING gin (keyword_tsv);

-- Table Triggers

create trigger tsvectorupdate before
insert
    or
update
    on
    public.universal_news for each row execute function tsvector_update_trigger('keyword_tsv', 'pg_catalog.english', 'keyword');


-- public.users definition

-- Drop table

-- DROP TABLE public.users;

CREATE TABLE public.users ( user_id varchar(256) NOT NULL, email varchar(255) NOT NULL, google_id varchar(255) NULL, full_name varchar(255) NULL, avatar_url text NULL, is_active bool DEFAULT true NOT NULL, created_at timestamptz DEFAULT now() NOT NULL, updated_at timestamptz DEFAULT now() NOT NULL, CONSTRAINT users_email_key UNIQUE (email), CONSTRAINT users_google_id_key UNIQUE (google_id), CONSTRAINT users_pkey PRIMARY KEY (user_id));
CREATE INDEX idx_users_google_id ON public.users USING btree (google_id);


-- public.investment_profiles definition

-- Drop table

-- DROP TABLE public.investment_profiles;

CREATE TABLE public.investment_profiles ( profile_id varchar(255) NOT NULL, user_id varchar(255) NOT NULL, profile_name varchar(100) NOT NULL, description text NULL, risk_tolerance jsonb NOT NULL, invest_goal jsonb NOT NULL, knowledge_exp jsonb NOT NULL, capital_income jsonb NOT NULL, personal_prefer jsonb NOT NULL, use_in_advisor bool DEFAULT true NOT NULL, is_default bool DEFAULT false NOT NULL, created_at timestamptz DEFAULT now() NOT NULL, updated_at timestamptz DEFAULT now() NOT NULL, CONSTRAINT investment_profiles_pkey PRIMARY KEY (profile_id), CONSTRAINT investment_profiles_user_id_profile_name_key UNIQUE (user_id, profile_name), CONSTRAINT investment_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE);
CREATE INDEX idx_investment_profiles_user_id ON public.investment_profiles USING btree (user_id);

-- Table Triggers

create trigger enforce_profile_limit before
insert
    on
    public.investment_profiles for each row execute function check_profile_limit();

-- public.backtest_reports definition

-- Drop table

-- DROP TABLE public.backtest_reports;

CREATE TABLE public.backtest_reports ( report_id varchar(256) NOT NULL, ticker varchar(10) NOT NULL, backtest_date timestamptz NOT NULL, report jsonb NOT NULL, created_at timestamptz DEFAULT now() NOT NULL, CONSTRAINT backtest_reports_pkey PRIMARY KEY (report_id), CONSTRAINT backtest_reports_ticker_fkey FOREIGN KEY (ticker) REFERENCES public.tickers(ticker_sym));
CREATE INDEX idx_analysis_reports_ticker_date ON public.backtest_reports USING btree (ticker, backtest_date DESC);


-- public.daily_prices definition

-- Drop table

-- DROP TABLE public.daily_prices;

CREATE TABLE public.daily_prices ( record_id int8 GENERATED BY DEFAULT AS IDENTITY( INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1 NO CYCLE) NOT NULL, "open" float4 NULL, high float4 NULL, low float4 NULL, "close" float4 NULL, volume float4 NULL, ticker varchar(12) NOT NULL, collect_date timestamptz NOT NULL, CONSTRAINT daily_prices_pkey PRIMARY KEY (record_id), CONSTRAINT daily_prices_unique UNIQUE (ticker, collect_date), CONSTRAINT daily_prices_ticker_fkey FOREIGN KEY (ticker) REFERENCES public.tickers(ticker_sym));
CREATE INDEX daily_prices_ticker ON public.daily_prices USING btree (ticker);


-- public.relevant_news definition

-- Drop table

-- DROP TABLE public.relevant_news;

CREATE TABLE public.relevant_news ( news_uuid varchar(256) NOT NULL, ticker varchar(10) NOT NULL, title text NOT NULL, summary text NULL, provider varchar(150) NULL, link text NULL, publish_time timestamptz NULL, collect_time timestamptz NOT NULL, CONSTRAINT relevant_news_pkey PRIMARY KEY (news_uuid), CONSTRAINT relevant_news_ticker_fkey FOREIGN KEY (ticker) REFERENCES public.tickers(ticker_sym));
CREATE INDEX relevant_news_ticker ON public.relevant_news USING btree (ticker);