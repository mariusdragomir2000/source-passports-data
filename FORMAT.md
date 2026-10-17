# Source Passports research batch: file format and rules

You are drafting records for a public register of who owns, funds and distributes the organisations that shape public information (news media, platforms, parties, regulators). Your output is imported into the register as "Pending check" and then verified by a researcher, so every fact must carry a source and nothing may be guessed.

## Output

A UTF-8 CSV file (comma separated, quoted where needed, multi-line cells allowed) with exactly these columns, in this order:

name, country, legal_name, brand_names, registration_number, registered_address, year_founded, media_type, editor_in_chief, contact_email, owners, beneficial_owners, state_ownership, parent_group, public_funding, revenue_mix, major_funders, domains, social_accounts, distribution_partners, sister_outlets, political_links, sources_origin, sources_control, sources_money, sources_channels, sources_distribution, sources_networks, research_notes

- `name` and `country` must be copied EXACTLY from the input list (they are the key that matches the existing record). Never rename.
- One row per organisation in the input list. Keep a row even if you found little; fill what you could.
- Leave a cell empty when you have no sourced fact. Empty is correct; a guess is wrong.

## Cell formats

Lists (one item per line inside the cell): `brand_names`, `domains` (bare hostnames such as `example.nl`, no https), `sister_outlets`.

Repeaters: one entry per line; parts separated by ` | ` in this order (leave a part empty if unknown, keep the separators):

- `owners`: `Owner name | share % as number (e.g. 51 or 33.3) | direct or indirect | person, company, state, fund, trust or other`
  List the owners that matter: anyone with 5% or more, the controlling owner, and the chain up to the ultimate parent (mark intermediate holdings as indirect).
- `beneficial_owners`: `Person | how control is held (e.g. "owns 100% of Holding B.V., the sole shareholder")`
  ONLY when an official register (company register, UBO register, regulator's licence file, stock-exchange filing) or the organisation itself names the person. A press report alone is not enough: put it in research_notes instead.
- `public_funding`: `year | state advertising amount | third-country public revenue amount | currency` (only amounts the organisation or a public body has published)
- `revenue_mix`: `advertising, readers, grants, public, owner or other | lt10, 10_25, 25_50 or gt50` (only if published in an annual report or disclosure page)
- `major_funders`: `Funder | foundation, company, government, individual or other | note`
- `social_accounts`: `Platform | full URL`
- `distribution_partners`: `Partner | role` (carriers, platforms, syndication; usually leave empty)
- `political_links`: `Person | role or office | period` — only documented public office or party roles of owners or executives, from official sources (parliament, government, party or company sites).

Single values:
- `state_ownership`: `none`, `minority`, `majority` or `full` (public bodies and public-service media are `full`; leave empty if unknown).
- `media_type` (media only): `online`, `newspaper`, `magazine`, `television`, `radio`, `news_agency`, `multi_platform` or `other`.
- `year_founded`: four digits. `registration_number`: as written in the register, with the register's label (e.g. `KvK 12345678`, `Org.nr 556001-2345`, `Companies House 01234567`, `SIREN 123 456 789`).
- `registered_address`: as in the register. `contact_email`: a general address published by the organisation (not a person's).
- `editor_in_chief`: the editor-in-chief for media, the head (director, chair, secretary-general) for other organisations, with the title in brackets.
- `parent_group`: the ultimate parent, with the chain in brackets if useful.

Sources (`sources_origin`, `sources_control`, `sources_money`, `sources_channels`, `sources_distribution`, `sources_networks`): one per line, format `Title or register, date (what it shows) | URL`. Every non-empty layer needs at least one source. Prefer, in this order: the national company register or UBO register; the regulator's licence register; the organisation's own ownership/transparency/About page (since August 2025 news media in the EU must publish ownership under EMFA Article 6); annual reports and stock-exchange filings; then reputable press for context only.

`research_notes` (private, not published): what you could not find, conflicts between sources, press-only claims, and anything a verifier should check first. Start it with `Drafted [date] by automated research; sources as listed.`

## Which columns apply to which kind

The register shows only the facts that fit the kind of organisation (plugin 1.5 and later). Do not spend time on columns marked "no": they are not shown for that kind. Values already present are kept in the data, never deleted.

| Column | Media | Platform | Business, agency | Party | Regulator, public body | Civil society, funder |
|---|---|---|---|---|---|---|
| media_type | yes | no | no | no | no | no |
| editor_in_chief (shown as) | Editor-in-chief | Chief executive | Chief executive | Leader | Head | Director or chair |
| owners | yes | yes | yes | no | owner or founding authority | founders or members with control |
| beneficial_owners | yes | yes | yes | no | no | yes |
| state_ownership | yes | yes | yes | no | yes | yes |
| parent_group (shown as) | parent group | parent group | parent group | European or international party family | answers to | network or umbrella organisation |
| public_funding (state advertising) | yes | no | no | no | no | no |
| revenue_mix | yes | yes | yes | income mix | how it is funded | income mix |
| major_funders | yes | investors and funders | investors and funders | state funding and named donors | budget and funding bodies | funders and donors |
| distribution_partners | yes | no | no | no | no | no |
| sister_outlets (shown as) | sister outlets | other services of the group | related companies | media, foundations and other bodies it controls | agencies and funds under it | no |
| political_links | yes | yes | yes | no | roles of board members | yes |

`revenue_mix` categories by kind (use these words in the first part):
- media and platforms: `advertising, readers, grants, public, owner, other`
- businesses and agencies: `advertising` (advertising), `readers` (subscriptions and user payments), `public` (public contracts and funding), `owner` (owner or group funding), `other` (sales, services and other)
- parties: `public` (state funding), `grants` (donations), `other` (membership fees and other income)
- regulators and public bodies: `public` (state budget), `other` (fees, levies and own income), `grants` (grants)
- civil society and funders: `grants` (grants and donations), `public` (public funding), `readers` (members and individual supporters), `other` (other income)

The European Media Freedom Act (EMFA) applies only to news media in the 27 EU member states. Do not cite it as the reason a non-EU outlet, or any organisation that is not a news medium, should disclose something. Outside the EU, the third part of `public_funding` means foreign (non-domestic) public funding.

## Rules

1. Primary sources first; copy names and numbers exactly as the source writes them.
2. Never infer ownership from a brand or a press rumour. If two sources disagree, record the official one in the field and the conflict in research_notes.
3. Public-service media: legal name and the law or charter that creates it; state_ownership `full`; head as editor_in_chief; funding in revenue_mix (`public | gt50`) with the annual report as source.
4. Platforms and foreign companies operating in a country: legal_name is the entity that serves users in that country (e.g. the EU subsidiary), parent_group the ultimate parent.
5. Do not include personal contact details of private individuals. Addresses are company addresses only.
6. Dates in sources matter: say when the page or filing was read or dated.
7. Write all text in English (names stay in the original language).
