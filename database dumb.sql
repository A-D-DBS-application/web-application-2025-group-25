-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.AI_partner (
  partner_id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  name text,
  contact_email text NOT NULL UNIQUE,
  CONSTRAINT AI_partner_pkey PRIMARY KEY (partner_id),
  CONSTRAINT AI_partner_partner_id_fkey FOREIGN KEY (partner_id) REFERENCES public.AI_solution(partner_id),
  CONSTRAINT AI_partner_partner_id_fkey1 FOREIGN KEY (partner_id) REFERENCES public.Parameter_value(partner_id)
);
CREATE TABLE public.AI_solution (
  solution_id bigint GENERATED ALWAYS AS IDENTITY NOT NULL UNIQUE,
  name text,
  description text UNIQUE,
  customer_cost double precision,
  partner_id bigint NOT NULL UNIQUE,
  created_at timestamp with time zone UNIQUE,
  CONSTRAINT AI_solution_pkey PRIMARY KEY (solution_id)
);
CREATE TABLE public.Calculator (
  calculator_id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  annual_net_profit double precision,
  Cost_saved_id bigint UNIQUE,
  solution_id bigint UNIQUE,
  CONSTRAINT Calculator_pkey PRIMARY KEY (calculator_id),
  CONSTRAINT Calculator_solution_id_fkey FOREIGN KEY (solution_id) REFERENCES public.AI_solution(solution_id),
  CONSTRAINT Calculator_Cost_saved_id_fkey FOREIGN KEY (Cost_saved_id) REFERENCES public.Costs_saved(Cost_saved_id)
);
CREATE TABLE public.Clustering_Result (
  clustering_result_id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  company_id bigint UNIQUE,
  calculator_id bigint UNIQUE,
  cluster_name text,
  CONSTRAINT Clustering_Result_pkey PRIMARY KEY (clustering_result_id),
  CONSTRAINT Clustering_Result_calculator_id_fkey FOREIGN KEY (calculator_id) REFERENCES public.Calculator(calculator_id),
  CONSTRAINT Clustering_Result_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.Company(company-id)
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
  parameters_id bigint UNIQUE,
  CONSTRAINT Costs_saved_pkey PRIMARY KEY (Cost_saved_id),
  CONSTRAINT Costs_saved_parameters_id_fkey FOREIGN KEY (parameters_id) REFERENCES public.Parameter_value(parameters_id),
  CONSTRAINT total_cost_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.Company(company-id)
);
CREATE TABLE public.Parameter_value (
  parameters_id bigint GENERATED ALWAYS AS IDENTITY NOT NULL UNIQUE,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  partner_id bigint NOT NULL UNIQUE,
  parameter_name text,
  parameter_value bigint,
  CONSTRAINT Parameter_value_pkey PRIMARY KEY (parameters_id)
);

CREATE TABLE public.Type_of_company (
  Type_of_company_id bigint GENERATED ALWAYS AS IDENTITY NOT NULL UNIQUE,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  sector text,
  CONSTRAINT Type_of_company_pkey PRIMARY KEY (Type_of_company_id)
);

CREATE TABLE public.payment_subscription (
  subscription_id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  start_date timestamp with time zone NOT NULL DEFAULT now(),
  partner_id bigint NOT NULL UNIQUE,
  plan_name text,
  status text,
  end_date timestamp with time zone,
  CONSTRAINT payment_subscription_pkey PRIMARY KEY (subscription_id),
  CONSTRAINT payment_subscription_partner_id_fkey FOREIGN KEY (partner_id) REFERENCES public.AI_partner(partner_id)
);
