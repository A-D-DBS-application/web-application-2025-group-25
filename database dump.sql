-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.AI_partner (
  partner_id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  name text,
  contact_email text NOT NULL UNIQUE,
  CONSTRAINT AI_partner_pkey PRIMARY KEY (partner_id),
  CONSTRAINT AI_partner_partner_id_fkey FOREIGN KEY (partner_id) REFERENCES public.AI_solution(partner_id),
  CONSTRAINT AI_partner_partner_id_fkey1 FOREIGN KEY (partner_id) REFERENCES public.Input_Parameter_Template(partner_id)
);
CREATE TABLE public.AI_solution (
  solution_id bigint GENERATED ALWAYS AS IDENTITY NOT NULL UNIQUE,
  name text NOT NULL,
  description text NOT NULL UNIQUE,
  customer_cost double precision,
  pricing_model text,
  partner_id bigint UNIQUE,
  CONSTRAINT AI_solution_pkey PRIMARY KEY (solution_id)
);
CREATE TABLE public.Calculator (
  calculator_id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  annuel_net_profit double precision,
  Cost_saved_id bigint UNIQUE,
  solution_id bigint UNIQUE,
  CONSTRAINT Calculator_pkey PRIMARY KEY (calculator_id),
  CONSTRAINT Calculator_solution_id_fkey FOREIGN KEY (solution_id) REFERENCES public.AI_solution(solution_id),
  CONSTRAINT Calculator_Cost_saved_id_fkey FOREIGN KEY (Cost_saved_id) REFERENCES public.Costs_saved(Cost_saved_id)
);
CREATE TABLE public.Company (
  company-id bigint GENERATED ALWAYS AS IDENTITY NOT NULL UNIQUE,
  created_at timestamp with time zone NOT NULL,
  name text,
  employee_count bigint,
  projects_per_year bigint NOT NULL,
  type_of_company_id bigint,
  CONSTRAINT Company_pkey PRIMARY KEY (company-id),
  CONSTRAINT Company_type_of_company_id_fkey FOREIGN KEY (type_of_company_id) REFERENCES public.Type_of_company(Type_of_company_id)
);
CREATE TABLE public.Costs_saved (
  Cost_saved_id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  created_at timestamp with time zone NOT NULL,
  company_id bigint NOT NULL,
  hours_spent_process double precision,
  materials_used_price bigint UNIQUE,
  parameters_id bigint UNIQUE,
  CONSTRAINT Costs_saved_pkey PRIMARY KEY (Cost_saved_id),
  CONSTRAINT Costs_saved_parameters_id_fkey FOREIGN KEY (parameters_id) REFERENCES public.Input_Parameter_Template(parameters_id),
  CONSTRAINT total_cost_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.Company(company-id),
  CONSTRAINT bespaarde_kosten_gebruik_matriaal_proces_fkey FOREIGN KEY (materials_used_price) REFERENCES public.Project(materials_used_price),
  CONSTRAINT bespaarde_kosten_verbruikt_matriaal_proces_fkey FOREIGN KEY (materials_used_price) REFERENCES public.Project(materials_used_price)
);
CREATE TABLE public.Employee (
  employee_id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  company_id bigint NOT NULL,
  name text,
  role text,
  wage_cost_per_hour double precision,
  is_active boolean,
  involved_in_process boolean NOT NULL,
  created_at timestamp with time zone,
  CONSTRAINT Employee_pkey PRIMARY KEY (employee_id),
  CONSTRAINT employee_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.Company(company-id)
);
CREATE TABLE public.Input_Parameter_Template (
  parameters_id bigint GENERATED ALWAYS AS IDENTITY NOT NULL UNIQUE,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  partner_id bigint NOT NULL UNIQUE,
  CONSTRAINT Input_Parameter_Template_pkey PRIMARY KEY (parameters_id),
  CONSTRAINT Input_Parameter_Template_parameters_id_fkey1 FOREIGN KEY (parameters_id) REFERENCES public.Parameter_value(parameters_id)
);
CREATE TABLE public.Parameter_value (
  Parameter_value_id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  parameter_name text,
  parameter_value bigint,
  parameters_id bigint UNIQUE,
  CONSTRAINT Parameter_value_pkey PRIMARY KEY (Parameter_value_id)
);
CREATE TABLE public.Pricing_ai_company (
  pricing_id bigint NOT NULL DEFAULT nextval('"Pricing_ai_company_pricing_id_seq"'::regclass),
  created_at timestamp with time zone NOT NULL,
  ai_service_cost bigint NOT NULL UNIQUE,
  CONSTRAINT Pricing_ai_company_pkey PRIMARY KEY (pricing_id)
);
CREATE TABLE public.Project (
  project_id bigint NOT NULL UNIQUE,
  created_at timestamp with time zone NOT NULL,
  company_id bigint,
  employee_id bigint UNIQUE,
  materials_used_price bigint UNIQUE,
  CONSTRAINT Project_pkey PRIMARY KEY (project_id),
  CONSTRAINT project_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.Employee(employee_id)
);
CREATE TABLE public.Type_of_company (
  Type_of_company_id bigint GENERATED ALWAYS AS IDENTITY NOT NULL UNIQUE,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  sector text,
  description text,
  CONSTRAINT Type_of_company_pkey PRIMARY KEY (Type_of_company_id)
);
CREATE TABLE public.kv_store_66f2438a (
  key text NOT NULL,
  value jsonb NOT NULL,
  CONSTRAINT kv_store_66f2438a_pkey PRIMARY KEY (key)
);
CREATE TABLE public.listing (
  id integer NOT NULL DEFAULT nextval('listing_id_seq'::regclass),
  listing_name character varying NOT NULL,
  price double precision NOT NULL,
  user_id integer NOT NULL,
  CONSTRAINT listing_pkey PRIMARY KEY (id),
  CONSTRAINT listing_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.user(id)
);
CREATE TABLE public.payment_subscription (
  subscription_id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  start_date timestamp with time zone NOT NULL DEFAULT now(),
  partner_id bigint NOT NULL UNIQUE,
  plan_name text,
  status text,
  end_date timestamp with time zone,
  pricing_id bigint UNIQUE,
  CONSTRAINT payment_subscription_pkey PRIMARY KEY (subscription_id),
  CONSTRAINT payment_subscription_partner_id_fkey FOREIGN KEY (partner_id) REFERENCES public.AI_partner(partner_id)
);
CREATE TABLE public.user (
  id integer NOT NULL DEFAULT nextval('user_id_seq'::regclass),
  email character varying NOT NULL UNIQUE,
  CONSTRAINT user_pkey PRIMARY KEY (id)
);
